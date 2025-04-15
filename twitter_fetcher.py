import time
import random
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException
)
from fake_useragent import UserAgent
import config
import logging
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            
            # Utilisation du ChromeDriver système
            service = Service(executable_path='/usr/bin/chromedriver')
            
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
            time.sleep(random.uniform(2, 4))
            
            # Entrée du nom d'utilisateur
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username_input.send_keys(self.username)
            self.driver.find_element(By.XPATH, '//span[text()="Next"]').click()
            time.sleep(random.uniform(1, 2))
            
            # Entrée du mot de passe
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
            )
            password_input.send_keys(self.password)
            self.driver.find_element(By.XPATH, '//span[text()="Log in"]').click()
            time.sleep(random.uniform(3, 5))
            
            logger.info("Connexion à Twitter réussie")
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à Twitter : {str(e)}")
            raise
        
    def scroll_page(self, driver, max_tweets=10):
        """Scroll progressif de la page pour charger plus de tweets."""
        tweets = set()
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 20
        no_new_tweets_count = 0
        
        while len(tweets) < max_tweets and scroll_attempts < max_attempts:
            try:
                # Scroll progressif avec vérification
                current_height = 0
                target_height = last_height
                
                for i in range(3):
                    current_height += target_height // 3
                    driver.execute_script(f"window.scrollTo(0, {current_height});")
                    time.sleep(0.5)
                    
                    # Vérification des nouveaux tweets
                    new_tweets = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                    if len(new_tweets) > len(tweets):
                        tweets = set(new_tweets)
                        no_new_tweets_count = 0
                        break
                
                # Vérification finale
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_new_tweets_count += 1
                else:
                    no_new_tweets_count = 0
                    last_height = new_height
                
                # Si pas de nouveaux tweets après plusieurs tentatives, on arrête
                if no_new_tweets_count >= 3:
                    break
                
                if len(tweets) >= max_tweets:
                    break
                    
                scroll_attempts += 1
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Erreur lors du scroll : {str(e)}")
                scroll_attempts += 1
                time.sleep(2)
        
        return list(tweets)[:max_tweets]

    def extract_tweet_data(self, tweet_element):
        """Extrait les données d'un tweet avec gestion des erreurs améliorée."""
        try:
            # Attente explicite pour les éléments avec retry
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    wait = WebDriverWait(tweet_element, 5)
                    
                    # Extraction du texte avec retry
                    text_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetText"]')))
                    text = text_element.text
                    
                    # Extraction de la date avec retry
                    date_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'time')))
                    date = date_element.get_attribute('datetime')
                    
                    # Extraction des métriques avec gestion des erreurs
                    metrics = {}
                    try:
                        metrics_elements = tweet_element.find_elements(By.CSS_SELECTOR, '[data-testid$="-count"]')
                        for element in metrics_elements:
                            metric_type = element.get_attribute('data-testid').replace('-count', '')
                            count = element.text
                            count = int(count.replace('K', '000').replace('M', '000000')) if count else 0
                            metrics[metric_type] = count
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'extraction des métriques : {str(e)}")
                    
                    # Extraction des hashtags
                    hashtags = []
                    try:
                        hashtag_elements = tweet_element.find_elements(By.CSS_SELECTOR, 'a[href^="/hashtag/"]')
                        hashtags = [tag.text for tag in hashtag_elements]
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'extraction des hashtags : {str(e)}")
                    
                    return {
                        'text': text,
                        'date': date,
                        'metrics': metrics,
                        'hashtags': hashtags
                    }
                    
                except (TimeoutException, StaleElementReferenceException) as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(1)
                        continue
                    raise
                    
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction des données du tweet : {str(e)}")
            return None
            
    def fetch_account_tweets(self, account: str, max_tweets: int = 10) -> List[Dict[str, Any]]:
        """Récupère les tweets d'un compte Twitter."""
        tweets = []
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Récupération des tweets de @{account}...")
                
                # Chargement de la page Twitter avec retry
                url = f"https://twitter.com/{account}"
                self.driver.get(url)
                
                # Attente du chargement initial avec retry
                initial_wait = WebDriverWait(self.driver, 20)
                initial_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]')))
                
                # Attente supplémentaire pour le chargement complet
                time.sleep(random.uniform(3, 5))
                
                # Scroll pour charger plus de tweets
                tweet_elements = self.scroll_page(self.driver, max_tweets)
                
                # Extraction des données des tweets
                for tweet_element in tweet_elements:
                    tweet_data = self.extract_tweet_data(tweet_element)
                    if tweet_data:
                        tweets.append(tweet_data)
                
                if tweets:
                    return tweets
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(f"Timeout lors de la récupération des tweets de {account} (tentative {retry_count}/{max_retries})")
                        time.sleep(random.uniform(5, 10))
                        continue
                    
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Timeout lors de la récupération des tweets de {account} (tentative {retry_count}/{max_retries})")
                    time.sleep(random.uniform(5, 10))
                    continue
                else:
                    logger.error(f"Échec de la récupération des tweets pour {account} après {max_retries} tentatives")
                    return []
        
        return tweets
            
    def fetch_all_accounts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Récupère les tweets de tous les comptes configurés."""
        from config import CRYPTO_ACCOUNTS
        
        all_tweets = {}
        
        try:
            # Connexion à Twitter
            self.login()
            
            # Récupération des tweets pour chaque compte
            for account in CRYPTO_ACCOUNTS:
                logger.info(f"Récupération des tweets de @{account}...")
                tweets = self.fetch_account_tweets(account)
                all_tweets[account] = tweets
                time.sleep(random.uniform(2, 4))
            
            return all_tweets
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tweets : {str(e)}")
            return all_tweets
            
        finally:
            if self.driver:
                self.driver.quit() 