import requests
import logging
import feedparser
from typing import Dict, Any, List
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import config

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataFetcher:
    def __init__(self):
        """Initialise le fetcher avec les configurations nécessaires."""
        load_dotenv()
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        
        # URLs des APIs
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.cryptopanic_rss_url = "https://cryptopanic.com/feed"
        
    def get_top_crypto_prices(self) -> Dict[str, Any]:
        """Récupère les prix des principales cryptos depuis CoinGecko."""
        try:
            logger.info("Récupération des prix des cryptos depuis CoinGecko")
            
            # Liste des cryptos à suivre
            crypto_ids = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']
            
            # Paramètres de la requête
            params = {
                'ids': ','.join(crypto_ids),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }
            
            # Ajout de la clé API si disponible
            if self.coingecko_api_key:
                params['x_cg_demo_api_key'] = self.coingecko_api_key
            
            response = requests.get(f"{self.coingecko_base_url}/simple/price", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Normalisation des données
            normalized_data = {
                "source": "coingecko",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prices": {},
                "market_caps": {},
                "changes_24h": {}
            }
            
            for crypto_id, crypto_data in data.items():
                normalized_data["prices"][crypto_id] = crypto_data.get('usd', 0)
                normalized_data["market_caps"][crypto_id] = crypto_data.get('usd_market_cap', 0)
                normalized_data["changes_24h"][crypto_id] = crypto_data.get('usd_24h_change', 0)
            
            logger.info("Données des prix récupérées avec succès")
            return normalized_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des prix : {str(e)}")
            return {
                "source": "coingecko",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
            
    def get_sentiment_metrics(self) -> Dict[str, Any]:
        """Récupère les métriques de sentiment depuis CryptoPanic RSS."""
        try:
            logger.info("Récupération des métriques de sentiment depuis CryptoPanic RSS")
            
            # Récupération du flux RSS
            feed = feedparser.parse(self.cryptopanic_rss_url)
            
            # Analyse des sentiments
            bullish_count = 0
            bearish_count = 0
            total_entries = len(feed.entries)
            
            for entry in feed.entries:
                if 'bullish' in entry.get('title', '').lower():
                    bullish_count += 1
                elif 'bearish' in entry.get('title', '').lower():
                    bearish_count += 1
            
            # Calcul du score de sentiment
            sentiment_score = 0
            if total_entries > 0:
                sentiment_score = (bullish_count - bearish_count) / total_entries
            
            # Normalisation des données
            normalized_data = {
                "source": "cryptopanic_rss",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {
                    "bullish_count": bullish_count,
                    "bearish_count": bearish_count,
                    "total_entries": total_entries,
                    "sentiment_score": sentiment_score
                }
            }
            
            logger.info("Métriques de sentiment récupérées avec succès")
            return normalized_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques de sentiment : {str(e)}")
            return {
                "source": "cryptopanic_rss",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
            
    def fetch_all_market_data(self) -> Dict[str, Any]:
        """Récupère toutes les données de marché."""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'prices': self.get_top_crypto_prices(),
            'sentiment': self.get_sentiment_metrics()
        } 