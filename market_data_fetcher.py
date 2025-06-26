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
        
        # URLs des APIs
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.cryptopanic_rss_url = "https://cryptopanic.com/feed"
        self.coinmarketcap_url = "https://pro-api.coinmarketcap.com/v1"
        self.whale_alert_rss = "https://whale-alert.io/feed"
        
        # Headers par défaut
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        
    def get_top_crypto_prices(self) -> Dict[str, Any]:
        """Récupère les prix des principales cryptos depuis CoinGecko."""
        try:
            logger.info("Récupération des prix des cryptos depuis CoinGecko")
            
            # Liste des cryptos à suivre
            crypto_ids = [
                'bitcoin', 'ethereum', 'binancecoin', 'solana', 'cardano', 
                'ripple', 'polkadot', 'dogecoin', 'avalanche-2', 'chainlink',
                'polygon', 'cosmos', 'arbitrum', 'optimism', 'aptos'
            ]
            
            # Paramètres de la requête
            params = {
                'ids': ','.join(crypto_ids),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }
            
            # Headers pour la requête
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(
                f"{self.coingecko_base_url}/simple/price",
                params=params,
                headers=self.headers,
                timeout=10
            )
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
                title = entry.get('title', '').lower()
                if 'bullish' in title:
                    bullish_count += 1
                elif 'bearish' in title:
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
            
    def get_whale_alerts(self) -> List[Dict[str, Any]]:
        """Récupère les alertes de baleines depuis Whale Alert RSS."""
        try:
            logger.info("Récupération des alertes de baleines")
            
            feed = feedparser.parse(self.whale_alert_rss)
            alerts = []
            
            for entry in feed.entries[:10]:
                alert = {
                    'title': entry.get('title', ''),
                    'description': entry.get('description', ''),
                    'published': entry.get('published', ''),
                    'link': entry.get('link', '')
                }
                
                # Extraction des montants et symboles depuis le titre
                import re
                match = re.search(r'([\d,]+(?:\.\d+)?)\s+(\w+)', entry.get('title', ''))
                if match:
                    alert['amount'] = match.group(1).replace(',', '')
                    alert['symbol'] = match.group(2)
                    
                    # Détection du type de transaction
                    title_lower = entry.get('title', '').lower()
                    if 'transferred' in title_lower:
                        alert['type'] = 'transfer'
                    elif 'minted' in title_lower:
                        alert['type'] = 'mint'
                    elif 'burned' in title_lower:
                        alert['type'] = 'burn'
                    else:
                        alert['type'] = 'unknown'
                
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des alertes de baleines : {str(e)}")
            return []
            
    def get_market_cap_data(self) -> Dict[str, Any]:
        """Récupère les données de capitalisation boursière."""
        try:
            logger.info("Récupération des données de capitalisation")
            
            response = requests.get(
                f"{self.coingecko_base_url}/global",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            global_data = data.get('data', {})
            
            return {
                'total_market_cap': global_data.get('total_market_cap', {}).get('usd', 0),
                'total_volume': global_data.get('total_volume', {}).get('usd', 0),
                'market_cap_percentage': global_data.get('market_cap_percentage', {}),
                'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
                'upcoming_icos': global_data.get('upcoming_icos', 0),
                'ongoing_icos': global_data.get('ongoing_icos', 0),
                'ended_icos': global_data.get('ended_icos', 0),
                'markets': global_data.get('markets', 0)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données globales : {str(e)}")
            return {}
            
    def get_trending_coins(self) -> List[Dict[str, Any]]:
        """Récupère les cryptos tendances."""
        try:
            logger.info("Récupération des cryptos tendances")
            
            response = requests.get(
                f"{self.coingecko_base_url}/search/trending",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            trending = []
            
            for coin in data.get('coins', [])[:10]:
                item = coin.get('item', {})
                trending.append({
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'symbol': item.get('symbol'),
                    'market_cap_rank': item.get('market_cap_rank'),
                    'price_btc': item.get('price_btc'),
                    'score': item.get('score')
                })
            
            return trending
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tendances : {str(e)}")
            return []
            
    def fetch_all_market_data(self) -> Dict[str, Any]:
        """Récupère toutes les données de marché."""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'prices': self.get_top_crypto_prices(),
            'sentiment': self.get_sentiment_metrics(),
            'whale_alerts': self.get_whale_alerts(),
            'market_cap': self.get_market_cap_data(),
            'trending': self.get_trending_coins()
        } 