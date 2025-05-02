import time
import random
import os
import shutil
from typing import List, Dict, Any
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging
from dotenv import load_dotenv
import config
import stat

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_valid_driver_path() -> str:
    """
    Recherche un chemin valide pour le chromedriver.
    
    Returns:
        str: Le chemin du chromedriver valide.
        
    Raises:
        RuntimeError: Si aucun chromedriver valide n'est trouvé.
    """
    try:
        # 1. Essayer d'installer via ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        
        # 2. Parcourir récursivement le dossier pour trouver le chromedriver
        def find_chromedriver(directory: str) -> str:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file == "chromedriver":
                        path = os.path.join(root, file)
                        # Vérifier si le fichier est exécutable
                        if os.access(path, os.X_OK):
                            return path
            return None
            
        chromedriver_path = find_chromedriver(driver_path)
        if chromedriver_path:
            return chromedriver_path
            
        # 3. Vérifier la variable d'environnement
        env_path = os.getenv('CHROMEDRIVER_PATH')
        if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
            return env_path
            
        # 4. Chercher dans le PATH système
        system_path = shutil.which("chromedriver")
        if system_path and os.access(system_path, os.X_OK):
            return system_path
            
        raise RuntimeError(
            "Aucun ChromeDriver valide trouvé. Veuillez :\n"
            "1. Vérifier l'installation de ChromeDriver\n"
            "2. Définir la variable d'environnement CHROMEDRIVER_PATH\n"
            "3. Ajouter ChromeDriver au PATH système"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche du ChromeDriver : {str(e)}")
        raise RuntimeError(f"Impossible de localiser ChromeDriver : {str(e)}")

class TwitterFetcher:
    def __init__(self):
        """Initialise le fetcher avec les configurations nécessaires."""
        load_dotenv()
        self.username = os.getenv('TWITTER_USERNAME')
        self.password = os.getenv('TWITTER_PASSWORD')
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Configure et initialise le WebDriver Chrome."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            path = get_valid_driver_path()
            logger.info("ChromeDriver utilisé : %s", path)
            service = Service(executable_path=path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("WebDriver initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du WebDriver : {str(e)}")
            raise
        
    def login(self):
        """Se connecte à Twitter."""
        try:
            self.driver.get('https://twitter.com/login')
            time.sleep(2)
            
            # Entrée du nom d'utilisateur
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username_input.clear()
            username_input.send_keys(self.username)
            
            # Attente et clic sur le bouton Next
            next_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//span[text()="Next"]'))
            )
            next_button.click()
            time.sleep(2)
            
            # Entrée du mot de passe
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
            )
            password_input.clear()
            password_input.send_keys(self.password)
            
            # Attente et clic sur le bouton Log in
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//span[text()="Log in"]'))
            )
            login_button.click()
            time.sleep(3)
            
            # Vérification de la connexion
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="SideNav_AccountSwitcher_Button"]'))
                )
                logger.info("Connexion à Twitter réussie")
            except TimeoutException:
                logger.error("Échec de la connexion à Twitter")
                raise
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à Twitter : {str(e)}")
            raise
        
    def scroll_page(self, max_tweets=10):
        """Scroll de la page pour charger plus de tweets."""
        tweets = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        attempts = 0
        
        while len(tweets) < max_tweets and attempts < 15:
            try:
                # Scroll avec une position aléatoire pour éviter la détection
                scroll_position = last_height - random.randint(100, 500)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(1)
                
                # Récupération des tweets
                new_tweets = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                if len(new_tweets) > len(tweets):
                    tweets = set(new_tweets)
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                
                attempts += 1
                
            except Exception as e:
                logger.warning(f"Erreur lors du scroll : {str(e)}")
                break
        
        return list(tweets)[:max_tweets]

    def extract_tweet_data(self, tweet_element):
        """Extrait les données d'un tweet."""
        try:
            # Extraction du texte
            text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
            text = text_element.text
            
            # Extraction de la date
            date_element = tweet_element.find_element(By.TAG_NAME, 'time')
            date = date_element.get_attribute('datetime')
            
            # Extraction des métriques
            metrics = {}
            metrics_elements = tweet_element.find_elements(By.CSS_SELECTOR, '[data-testid$="-count"]')
            for element in metrics_elements:
                metric_type = element.get_attribute('data-testid').replace('-count', '')
                count = element.text
                count = int(count.replace('K', '000').replace('M', '000000')) if count else 0
                metrics[metric_type] = count
            
            # Extraction des hashtags
            hashtags = [tag.text for tag in tweet_element.find_elements(By.CSS_SELECTOR, 'a[href^="/hashtag/"]')]
            
            return {
                'text': text,
                'date': date,
                'metrics': metrics,
                'hashtags': hashtags
            }
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction des données du tweet : {str(e)}")
            return None
            
    def fetch_account_tweets(self, account: str, max_tweets: int = 10) -> List[Dict[str, Any]]:
        """Récupère les tweets d'un compte Twitter."""
        try:
            logger.info(f"Récupération des tweets de @{account}...")
            
            # Chargement de la page
            self.driver.get(f"https://twitter.com/{account}")
            time.sleep(2)
            
            # Attente du chargement initial
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
                )
            except TimeoutException:
                logger.warning(f"Timeout lors du chargement des tweets de {account}")
                return []
            
            # Récupération des tweets
            tweet_elements = self.scroll_page(max_tweets)
            tweets = []
            
            for tweet_element in tweet_elements:
                tweet_data = self.extract_tweet_data(tweet_element)
                if tweet_data:
                    tweets.append(tweet_data)
            
            logger.info(f"{len(tweets)} tweets récupérés pour @{account}")
            return tweets
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tweets de {account}: {str(e)}")
            return []
            
    def fetch_all_accounts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Récupère les tweets de tous les comptes configurés."""
        all_tweets = {}
        
        try:
            # Connexion à Twitter
            self.login()
            
            # Récupération des tweets pour chaque compte
            for account in config.CRYPTO_ACCOUNTS:
                tweets = self.fetch_account_tweets(account)
                all_tweets[account] = tweets
                time.sleep(2)  # Délai entre les comptes
            
            return all_tweets
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tweets : {str(e)}")
            return all_tweets
            
        finally:
            if self.driver:
                self.driver.quit() 