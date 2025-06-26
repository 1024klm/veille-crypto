import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration Twitter
TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')
TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')

# Configuration Twitter API
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Liste des comptes à surveiller
CRYPTO_ACCOUNTS = [
    'DeepWhale_',
    'LeJournalDuCoin',
    'coinacademy_fr',
    'CryptoastMedia',
    'MRadarCrypto',
    'GoodValueCrypto',
    'crypto_futur',
    'coinacademy_ia',
    'PowerPasheur',
    'LeBinanceFR',
    'coinbase',
    'bitgetglobal',
    'binance'
]

# Répertoire de sauvegarde des données
DATA_DIR = 'data'

# Paramètres de récupération
TWEETS_PER_ACCOUNT = 10
MAX_RETRIES = 3
RETRY_DELAY = 5  # secondes

# Paramètres de résumé
MIN_TWEETS_FOR_SUMMARY = 3
MAX_HASHTAGS = 5 