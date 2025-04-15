import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import concurrent.futures
import time

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
        # Liste des flux RSS crypto à suivre
        return [
            "https://cointelegraph.com/rss",
            "https://decrypt.co/feed",
            "https://cryptonews.com/news/feed/",
            "https://www.theblock.co/rss.xml",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://bitcoinmagazine.com/.rss/full/",
            "https://cryptoslate.com/feed/"
        ]
        
    def _process_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Traite un flux RSS individuel."""
        try:
            logger.info(f"Récupération du flux RSS : {feed_url}")
            
            # Ajout d'un délai pour éviter les limitations de taux
            time.sleep(1)
            
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Erreur de parsing pour le flux {feed_url}: {feed.bozo_exception}")
                return []
            
            entries = []
            for entry in feed.entries[:10]:  # Limite aux 10 dernières entrées
                try:
                    entry_data = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', datetime.now().isoformat()),
                        'summary': entry.get('summary', ''),
                        'source': feed_url
                    }
                    entries.append(entry_data)
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement d'une entrée du flux {feed_url}: {str(e)}")
                    continue
            
            logger.info(f"Récupération réussie pour {feed_url}: {len(entries)} entrées")
            return entries
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du flux {feed_url}: {str(e)}")
            return []
        
    def fetch_feeds(self) -> List[Dict[str, Any]]:
        """Récupère les entrées de tous les flux RSS en parallèle."""
        all_entries = []
        
        # Utilisation de ThreadPoolExecutor pour les requêtes parallèles
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Soumission de toutes les tâches
            future_to_url = {executor.submit(self._process_feed, url): url for url in self.feeds}
            
            # Récupération des résultats
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    entries = future.result()
                    all_entries.extend(entries)
                except Exception as e:
                    logger.error(f"Erreur lors du traitement du flux {url}: {str(e)}")
        
        # Tri des entrées par date de publication
        all_entries.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        logger.info(f"Total des entrées RSS récupérées: {len(all_entries)}")
        return all_entries
        
    def fetch_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Récupère les entrées d'un flux RSS spécifique."""
        return self._process_feed(feed_url) 