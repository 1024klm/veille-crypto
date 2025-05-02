import requests
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import config
from utils import require_api_key

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataFetcher:
    def __init__(self):
        """Initialise le fetcher avec les clés API nécessaires."""
        load_dotenv()
        self.glassnode_api_key = os.getenv('GLASSNODE_API_KEY')
        self.whale_alert_api_key = os.getenv('WHALE_ALERT_API_KEY')
        
        # URLs des APIs
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.glassnode_base_url = "https://api.glassnode.com/v1"
        self.whale_alert_base_url = "https://api.whale-alert.io/v1"
        
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
            
            # Utilisation de l'API publique
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
    
    @require_api_key('WHALE_ALERT_API_KEY')
    def get_whale_transactions(self) -> List[Dict[str, Any]]:
        """Récupère les transactions de baleines depuis Whale Alert."""
        try:
            logger.info("Récupération des transactions de baleines")
            
            url = f"{self.whale_alert_base_url}/transactions"
            params = {
                'api_key': self.whale_alert_api_key,
                'min_value': 1000000,  # 1M USD
                'limit': 10
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            transactions = []
            
            for tx in data.get('transactions', []):
                normalized_tx = {
                    'source': 'whale_alert',
                    'timestamp': tx.get('timestamp'),
                    'from': tx.get('from'),
                    'to': tx.get('to'),
                    'amount': tx.get('amount'),
                    'symbol': tx.get('symbol'),
                    'usd_value': tx.get('usd_value')
                }
                transactions.append(normalized_tx)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des transactions de baleines : {str(e)}")
            return []
    
    @require_api_key('GLASSNODE_API_KEY')
    def get_sentiment_metrics(self) -> Dict[str, Any]:
        """Récupère les métriques de sentiment depuis Glassnode."""
        try:
            logger.info("Récupération des métriques de sentiment")
            
            # Paramètres de la requête
            params = {
                'api_key': self.glassnode_api_key,
                'a': 'BTC'  # Bitcoin comme référence
            }
            
            # Récupération de plusieurs métriques
            metrics = {}
            
            # Fear & Greed Index
            response = requests.get(
                f"{self.glassnode_base_url}/indicators/fear_and_greed_index",
                params=params
            )
            if response.status_code == 200:
                metrics['fear_and_greed'] = response.json()
            
            # Network Value to Transactions Ratio (NVT)
            response = requests.get(
                f"{self.glassnode_base_url}/indicators/nvt",
                params=params
            )
            if response.status_code == 200:
                metrics['nvt'] = response.json()
            
            # Normalisation des données
            normalized_data = {
                "source": "glassnode",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": metrics
            }
            
            logger.info("Métriques de sentiment récupérées avec succès")
            return normalized_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques de sentiment : {str(e)}")
            return {
                "source": "glassnode",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    def fetch_all_market_data(self) -> Dict[str, Any]:
        """Récupère toutes les données de marché."""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sentiment': self.get_sentiment_metrics(),
            'whale_transactions': self.get_whale_transactions()
        } 