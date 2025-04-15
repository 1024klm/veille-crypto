import tweepy
import logging
from typing import List, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
import config

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterFetcher:
    def __init__(self):
        """Initialise le fetcher avec les clés API Twitter."""
        load_dotenv()
        
        # Récupération des clés API depuis les variables d'environnement
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        # Vérification des clés API
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret, self.bearer_token]):
            logger.error("Clés API Twitter manquantes dans le fichier .env")
            raise ValueError("Clés API Twitter manquantes")
        
        # Initialisation du client Twitter
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
        
        logger.info("Client Twitter initialisé avec succès")
    
    def fetch_account_tweets(self, account: str, max_tweets: int = 10) -> List[Dict[str, Any]]:
        """Récupère les tweets d'un compte Twitter."""
        try:
            logger.info(f"Récupération des tweets de @{account}...")
            
            # Récupération des tweets
            tweets = self.client.get_user_tweets(
                username=account,
                max_results=max_tweets,
                tweet_fields=['created_at', 'public_metrics', 'entities']
            )
            
            if not tweets.data:
                logger.warning(f"Aucun tweet trouvé pour @{account}")
                return []
            
            # Normalisation des données
            normalized_tweets = []
            for tweet in tweets.data:
                # Extraction des hashtags
                hashtags = []
                if hasattr(tweet, 'entities') and 'hashtags' in tweet.entities:
                    hashtags = [tag['tag'] for tag in tweet.entities['hashtags']]
                
                # Création du tweet normalisé
                normalized_tweet = {
                    'text': tweet.text,
                    'date': tweet.created_at.isoformat(),
                    'metrics': {
                        'retweet_count': tweet.public_metrics['retweet_count'],
                        'reply_count': tweet.public_metrics['reply_count'],
                        'like_count': tweet.public_metrics['like_count'],
                        'quote_count': tweet.public_metrics['quote_count']
                    },
                    'hashtags': hashtags
                }
                normalized_tweets.append(normalized_tweet)
            
            logger.info(f"{len(normalized_tweets)} tweets récupérés pour @{account}")
            return normalized_tweets
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tweets de {account}: {str(e)}")
            return []
    
    def fetch_all_accounts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Récupère les tweets de tous les comptes configurés."""
        all_tweets = {}
        
        try:
            # Récupération des tweets pour chaque compte
            for account in config.CRYPTO_ACCOUNTS:
                tweets = self.fetch_account_tweets(account)
                all_tweets[account] = tweets
            
            return all_tweets
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tweets : {str(e)}")
            return all_tweets 