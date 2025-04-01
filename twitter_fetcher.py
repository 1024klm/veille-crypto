import time
import random
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
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterFetcher:
    def __init__(self):
        """Initialise le webdriver Chrome avec les options appropriées."""
        self.setup_driver()
        self.login()
        
    def setup_driver(self):
        """Configure et initialise le webdriver Chrome avec des options optimisées."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Mode sans interface graphique
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={UserAgent().random}')
        
        # Désactivation des images pour accélérer le chargement
        prefs = {
            "profile.managed_default_content_settings.images": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Initialisation du driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)  # Attente implicite de 10 secondes
        
    def login(self):
        """Se connecte à Twitter avec les identifiants fournis."""
        try:
            logger.info("Tentative de connexion à Twitter...")
            self.driver.get("https://twitter.com/login")
            
            # Attente du chargement de la page de connexion
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            
            # Saisie du nom d'utilisateur
            username_input = self.driver.find_element(By.NAME, "text")
            username_input.send_keys(config.TWITTER_USERNAME)
            username_input.send_keys(Keys.RETURN)
            
            # Attente et saisie du mot de passe
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(config.TWITTER_PASSWORD)
            password_input.send_keys(Keys.RETURN)
            
            # Attente de la connexion réussie
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-testid='primaryColumn']"))
            )
            
            logger.info("Connexion à Twitter réussie")
            time.sleep(2)  # Pause pour laisser le temps à la page de se stabiliser
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à Twitter: {str(e)}")
            raise
        
    def scroll_page(self, scroll_count: int = 5):
        """Fait défiler la page un nombre spécifié de fois."""
        for _ in range(scroll_count):
            # Scroll jusqu'au bas de la page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Attente aléatoire entre 1 et 3 secondes
            time.sleep(random.uniform(1, 3))
            
    def extract_tweet_data(self, tweet_element) -> Optional[Dict[str, Any]]:
        """Extrait les données d'un tweet à partir de son élément HTML."""
        try:
            # Sélecteurs pour les différents éléments du tweet
            text_selector = "//div[@data-testid='tweetText']"
            date_selector = "//time"
            metrics_selector = "//div[@data-testid='like']//span"
            
            # Extraction du texte
            text_element = tweet_element.find_element(By.XPATH, text_selector)
            text = text_element.text
            
            # Extraction de la date
            date_element = tweet_element.find_element(By.XPATH, date_selector)
            date = date_element.get_attribute('datetime')
            
            # Extraction des métriques (likes, retweets, etc.)
            metrics = {}
            try:
                metrics_elements = tweet_element.find_elements(By.XPATH, metrics_selector)
                metrics = {
                    'like_count': int(metrics_elements[0].text) if metrics_elements[0].text else 0,
                    'retweet_count': int(metrics_elements[1].text) if metrics_elements[1].text else 0,
                    'reply_count': int(metrics_elements[2].text) if metrics_elements[2].text else 0
                }
            except (IndexError, ValueError):
                pass
            
            # Extraction des hashtags
            hashtags = []
            try:
                hashtag_elements = tweet_element.find_elements(By.XPATH, "//a[contains(@href, '/hashtag/')]")
                hashtags = [tag.text for tag in hashtag_elements]
            except:
                pass
            
            return {
                'text': text,
                'created_at': date,
                'metrics': metrics,
                'hashtags': hashtags
            }
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction des données du tweet: {str(e)}")
            return None
            
    def fetch_tweets(self, username: str, max_tweets: int = config.TWEETS_PER_ACCOUNT) -> List[Dict[str, Any]]:
        """Récupère les tweets d'un utilisateur via Selenium."""
        tweets = []
        url = f"https://twitter.com/{username}"
        
        try:
            logger.info(f"Accès au profil de {username}")
            self.driver.get(url)
            
            # Attente du chargement initial des tweets
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//article[@data-testid='tweet']"))
            )
            
            # Calcul du nombre de scrolls nécessaires
            scroll_count = max(1, max_tweets // 3)  # Environ 3 tweets par scroll
            
            # Récupération des tweets
            while len(tweets) < max_tweets:
                # Scroll de la page
                self.scroll_page(scroll_count)
                
                # Extraction des tweets visibles
                tweet_elements = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
                
                for tweet_element in tweet_elements:
                    if len(tweets) >= max_tweets:
                        break
                        
                    tweet_data = self.extract_tweet_data(tweet_element)
                    if tweet_data:
                        tweets.append(tweet_data)
                
                # Vérification si de nouveaux tweets ont été chargés
                if len(tweet_elements) <= len(tweets):
                    break
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tweets pour {username}: {str(e)}")
            
        return tweets[:max_tweets]
        
    def fetch_all_accounts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Récupère les tweets de tous les comptes configurés."""
        all_tweets = {}
        
        try:
            for account in config.CRYPTO_ACCOUNTS:
                logger.info(f"Récupération des tweets pour {account}")
                tweets = self.fetch_tweets(account)
                all_tweets[account] = tweets
                # Pause aléatoire entre les comptes
                time.sleep(random.uniform(2, 4))
                
        finally:
            # Fermeture du driver à la fin
            self.driver.quit()
            
        return all_tweets 