import os
import logging
import feedparser
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from pytrends.request import TrendReq
from dotenv import load_dotenv
import time
import random
from utils import require_api_key

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExternalSourcesFetcher:
    def __init__(self):
        """Initialise le fetcher avec les configurations nécessaires."""
        load_dotenv()
        self.cryptopanic_api_key = os.getenv('CRYPTOPANIC_API_KEY')
        self.lunarcrush_api_key = os.getenv('LUNARCRUSH_API_KEY')
        self.dune_analytics_api_key = os.getenv('DUNE_ANALYTICS_API_KEY')
        
        # Configuration des flux RSS
        self.rss_feeds = {
            'regulatory': {
                'sec': 'https://www.sec.gov/news/pressreleases.rss',
                'cftc': 'https://www.cftc.gov/rss/rss.xml',
                'esma': 'https://www.esma.europa.eu/rss.xml',
                'imf': 'https://www.imf.org/en/News/rss'
            },
            'exchanges': {
                'binance': 'https://www.binance.com/en/blog/rss',
                'coinbase': 'https://blog.coinbase.com/feed'
            },
            'community': {
                'hackernoon': 'https://hackernoon.com/feed'
            }
        }
        
        # Configuration des URLs pour le scraping
        self.scraping_urls = {
            'ecb': 'https://www.ecb.europa.eu/press/html/index.en.html',
            'bitcointalk': 'https://bitcointalk.org/index.php?board=7.0',
            'bitinfocharts': 'https://bitinfocharts.com/'
        }
        
        # Configuration des mots-clés pour Google Trends
        self.trend_keywords = ['bitcoin', 'ethereum', 'cryptocurrency', 'blockchain']
        
    def fetch_rss_feed(self, url: str, source: str) -> List[Dict[str, Any]]:
        """Récupère et parse un flux RSS."""
        try:
            feed = feedparser.parse(url)
            entries = []
            
            for entry in feed.entries[:10]:  # Limite aux 10 dernières entrées
                normalized_entry = {
                    'source': source,
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', ''),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                entries.append(normalized_entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du flux RSS {url}: {str(e)}")
            return []
            
    def fetch_google_trends(self) -> Dict[str, Any]:
        """Récupère les tendances Google pour les mots-clés configurés."""
        try:
            pytrends = TrendReq(hl=os.getenv('GOOGLE_TRENDS_GEO', 'FR'))
            
            # Construction de la requête
            timeframe = os.getenv('GOOGLE_TRENDS_TIMEFRAME', 'now 7-d')
            pytrends.build_payload(
                self.trend_keywords,
                timeframe=timeframe,
                geo=os.getenv('GOOGLE_TRENDS_GEO', 'FR')
            )
            
            # Récupération des données
            interest_over_time = pytrends.interest_over_time()
            
            # Normalisation des données
            trends_data = {
                'source': 'google_trends',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'keywords': self.trend_keywords,
                'data': interest_over_time.to_dict() if not interest_over_time.empty else {}
            }
            
            return trends_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tendances Google: {str(e)}")
            return {
                'source': 'google_trends',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }
            
    @require_api_key('CRYPTOPANIC_API_KEY')
    def fetch_cryptopanic_data(self) -> List[Dict[str, Any]]:
        """Récupère les données depuis CryptoPanic."""
        try:
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token={self.cryptopanic_api_key}"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Normalisation des données
            normalized_posts = []
            for post in data.get('results', []):
                normalized_post = {
                    'source': 'cryptopanic',
                    'title': post.get('title', ''),
                    'url': post.get('url', ''),
                    'published_at': post.get('published_at', ''),
                    'source_title': post.get('source', {}).get('title', ''),
                    'sentiment': post.get('sentiment', ''),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                normalized_posts.append(normalized_post)
            
            return normalized_posts
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données CryptoPanic: {str(e)}")
            return []
            
    @require_api_key('LUNARCRUSH_API_KEY')
    def fetch_lunarcrush_data(self) -> Dict[str, Any]:
        """Récupère les données depuis LunarCrush."""
        try:
            url = "https://api.lunarcrush.com/v2"
            params = {
                'data': 'assets',
                'key': self.lunarcrush_api_key,
                'symbol': 'BTC,ETH'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'source': 'lunarcrush',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données LunarCrush: {str(e)}")
            return {}
            
    def scrape_ecb_press(self) -> List[Dict[str, Any]]:
        """Scrape les communiqués de presse de la BCE."""
        try:
            response = requests.get(self.scraping_urls['ecb'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            press_items = soup.find_all('div', class_='press-item')
            
            normalized_items = []
            for item in press_items[:10]:  # Limite aux 10 derniers communiqués
                title = item.find('h2')
                date = item.find('time')
                link = item.find('a')
                
                if title and date and link:
                    normalized_item = {
                        'source': 'ecb',
                        'title': title.text.strip(),
                        'date': date.text.strip(),
                        'link': link.get('href', ''),
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    normalized_items.append(normalized_item)
            
            return normalized_items
            
        except Exception as e:
            logger.error(f"Erreur lors du scraping des communiqués BCE: {str(e)}")
            return []
            
    def fetch_all_sources(self) -> Dict[str, Any]:
        """Récupère toutes les sources externes."""
        all_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'regulatory': [],
            'exchanges': [],
            'community': [],
            'trends': {},
            'news': [],
            'social': {}
        }
        
        # Récupération des flux RSS réglementaires
        for source, url in self.rss_feeds['regulatory'].items():
            all_data['regulatory'].extend(self.fetch_rss_feed(url, source))
            
        # Récupération des flux RSS des exchanges
        for source, url in self.rss_feeds['exchanges'].items():
            all_data['exchanges'].extend(self.fetch_rss_feed(url, source))
            
        # Récupération des flux RSS communautaires
        for source, url in self.rss_feeds['community'].items():
            all_data['community'].extend(self.fetch_rss_feed(url, source))
            
        # Récupération des tendances Google
        all_data['trends'] = self.fetch_google_trends()
        
        # Récupération des données CryptoPanic
        all_data['news'].extend(self.fetch_cryptopanic_data())
        
        # Récupération des données LunarCrush
        all_data['social'] = self.fetch_lunarcrush_data()
        
        # Récupération des communiqués BCE
        all_data['regulatory'].extend(self.scrape_ecb_press())
        
        return all_data 

if __name__ == "__main__":
    try:
        logger.info("Démarrage des tests de ExternalSourcesFetcher...")
        
        # Instanciation du fetcher
        fetcher = ExternalSourcesFetcher()
        
        # Récupération des données
        logger.info("Récupération des données depuis toutes les sources...")
        data = fetcher.fetch_all_sources()
        
        # Affichage des statistiques
        logger.info("\nRésultats par catégorie :")
        logger.info(f"Réglementaire : {len(data['regulatory'])} items")
        logger.info(f"Exchanges : {len(data['exchanges'])} items")
        logger.info(f"Communauté : {len(data['community'])} items")
        logger.info(f"Tendances : {len(data['trends'].get('data', {}))} points de données")
        logger.info(f"Actualités : {len(data['news'])} items")
        
        logger.info("\nTest terminé avec succès !")
        
    except KeyError as e:
        logger.error(f"Erreur de clé : {str(e)}")
        logger.error("Structure de données inattendue")
        exit(1)
        
    except TimeoutError as e:
        logger.error(f"Timeout : {str(e)}")
        logger.error("Une requête a dépassé le temps imparti")
        exit(1)
        
    except Exception as e:
        logger.error(f"Erreur inattendue : {str(e)}")
        exit(1) 