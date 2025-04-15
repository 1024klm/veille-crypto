import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RSSFetcher:
    def __init__(self):
        """Initialise le fetcher RSS avec les configurations nécessaires."""
        load_dotenv()
        self.feeds = self._load_feed_urls()
        
    def _load_feed_urls(self) -> List[str]:
        """Charge les URLs des flux RSS depuis la configuration."""
        # TODO: Charger depuis un fichier de configuration ou .env
        return [
            "https://cointelegraph.com/rss",
            "https://decrypt.co/feed",
            "https://cryptonews.com/news/feed/",
            "https://www.theblock.co/rss.xml"
        ]
        
    def fetch_feeds(self) -> List[Dict[str, Any]]:
        """Récupère les entrées de tous les flux RSS configurés."""
        all_entries = []
        
        for feed_url in self.feeds:
            try:
                logger.info(f"Récupération du flux RSS : {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    processed_entry = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', datetime.now().isoformat()),
                        'summary': entry.get('summary', ''),
                        'source': feed_url
                    }
                    all_entries.append(processed_entry)
                    
            except Exception as e:
                logger.error(f"Erreur lors de la récupération du flux {feed_url}: {str(e)}")
                continue
                
        return all_entries
        
    def fetch_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Récupère les entrées d'un flux RSS spécifique."""
        try:
            logger.info(f"Récupération du flux RSS : {feed_url}")
            feed = feedparser.parse(feed_url)
            
            entries = []
            for entry in feed.entries:
                processed_entry = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', datetime.now().isoformat()),
                    'summary': entry.get('summary', ''),
                    'source': feed_url
                }
                entries.append(processed_entry)
                
            return entries
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du flux {feed_url}: {str(e)}")
            return [] 