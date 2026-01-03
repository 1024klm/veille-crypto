import os
import logging
import feedparser
import requests
from typing import Dict, List, Any
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from pytrends.request import TrendReq
from dotenv import load_dotenv
import time
import random
import config

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExternalSourcesFetcher:
    def __init__(self):
        """Initialise le fetcher avec les configurations nécessaires."""
        load_dotenv()
        
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
                'coinbase': 'https://blog.coinbase.com/feed',
                'bitget': 'https://www.bitget.com/blog/rss'
            },
            'media': {
                'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss',
                'cointelegraph': 'https://cointelegraph.com/rss',
                'decrypt': 'https://decrypt.co/feed',
                'bitcoin_magazine': 'https://bitcoinmagazine.com/.rss/full/',
                'theblock': 'https://www.theblock.co/rss.xml',
                'cryptoslate': 'https://cryptoslate.com/feed/',
                'cryptobriefing': 'https://cryptobriefing.com/feed/',
                'messari': 'https://messari.io/rss',
                'chainalysis': 'https://blog.chainalysis.com/reports/feed/'
            },
            'newsletters': {
                'thedefiant': 'https://thedefiant.io/feed',
                'banklesshq': 'https://newsletter.banklesshq.com/feed'
            },
            'analytics': {
                'glassnode': 'https://insights.glassnode.com/rss/',
                'santiment': 'https://insights.santiment.net/feed',
                'intotheblock': 'https://blog.intotheblock.com/feed/'
            },
            'community': {
                'hackernoon': 'https://hackernoon.com/feed',
                'bitcointalk': 'https://bitcointalk.org/index.php?action=.xml;board=1;limit=20;type=rss'
            },
            'french': {
                'journalducoin': 'https://journalducoin.com/feed/',
                'cryptoast': 'https://cryptoast.fr/feed/',
                'coinacademy': 'https://coinacademy.fr/feed/'
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

            # Conversion des données avec gestion des Timestamps
            trends_dict = {}
            if not interest_over_time.empty:
                # Conversion du DataFrame en dict avec des clés string (ISO format)
                for column in interest_over_time.columns:
                    if column != 'isPartial':
                        trends_dict[column] = {
                            ts.isoformat() if hasattr(ts, 'isoformat') else str(ts): int(val)
                            for ts, val in interest_over_time[column].items()
                        }

            # Normalisation des données
            trends_data = {
                'source': 'google_trends',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'keywords': self.trend_keywords,
                'data': trends_dict
            }

            return trends_data

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tendances Google: {str(e)}")
            return {
                'source': 'google_trends',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }
            
    def get_regulatory_news(self) -> List[Dict[str, Any]]:
        """Récupère les nouvelles réglementaires."""
        regulatory_news = []
        for source, url in self.rss_feeds['regulatory'].items():
            regulatory_news.extend(self.fetch_rss_feed(url, source))
        return regulatory_news
        
    def get_exchange_blog_posts(self) -> List[Dict[str, Any]]:
        """Récupère les posts de blog des exchanges."""
        exchange_posts = []
        for source, url in self.rss_feeds['exchanges'].items():
            exchange_posts.extend(self.fetch_rss_feed(url, source))
        return exchange_posts
        
    def get_community_posts(self) -> List[Dict[str, Any]]:
        """Récupère les posts de la communauté."""
        community_posts = []
        for source, url in self.rss_feeds['community'].items():
            community_posts.extend(self.fetch_rss_feed(url, source))
        return community_posts
        
    def get_media_news(self) -> List[Dict[str, Any]]:
        """Récupère les nouvelles des médias spécialisés."""
        media_news = []
        for source, url in self.rss_feeds['media'].items():
            media_news.extend(self.fetch_rss_feed(url, source))
        return media_news
        
    def get_newsletter_content(self) -> List[Dict[str, Any]]:
        """Récupère le contenu des newsletters."""
        newsletter_content = []
        for source, url in self.rss_feeds['newsletters'].items():
            newsletter_content.extend(self.fetch_rss_feed(url, source))
        return newsletter_content
        
    def get_analytics_insights(self) -> List[Dict[str, Any]]:
        """Récupère les analyses et insights."""
        analytics = []
        for source, url in self.rss_feeds['analytics'].items():
            analytics.extend(self.fetch_rss_feed(url, source))
        return analytics
        
    def get_french_news(self) -> List[Dict[str, Any]]:
        """Récupère les actualités en français."""
        french_news = []
        for source, url in self.rss_feeds['french'].items():
            french_news.extend(self.fetch_rss_feed(url, source))
        return french_news
            
    def fetch_all_sources(self) -> Dict[str, Any]:
        """Récupère toutes les sources externes."""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'regulatory': self.get_regulatory_news(),
            'exchange': self.get_exchange_blog_posts(),
            'media': self.get_media_news(),
            'newsletters': self.get_newsletter_content(),
            'analytics': self.get_analytics_insights(),
            'community': self.get_community_posts(),
            'french': self.get_french_news(),
            'trends': self.fetch_google_trends()
        }

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
        logger.info(f"Exchanges : {len(data['exchange'])} items")
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