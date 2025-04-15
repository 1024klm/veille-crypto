from typing import List, Dict, Any
import nltk
from collections import Counter
import config
import logging
import time
from nltk.tokenize import sent_tokenize
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TweetSummarizer:
    def __init__(self):
        # Téléchargement des ressources NLTK nécessaires
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        # Cache pour les résumés avec TTL
        self._cache = {}
        self._cache_timeout = 3600  # 1 heure
        self._cache_cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()
        self.logger = logging.getLogger(__name__)

    def _cleanup_cache(self):
        """Nettoie les entrées expirées du cache."""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cache_cleanup_interval:
            expired_keys = []
            for key, (_, timestamp) in self._cache.items():
                if current_time - timestamp > self._cache_timeout:
                    expired_keys.append(key)
            for key in expired_keys:
                del self._cache[key]
            self._last_cleanup = current_time

    def analyze_tweets(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse une liste de tweets pour générer un résumé."""
        # Nettoyage du cache
        self._cleanup_cache()
        
        # Vérification du cache
        cache_key = hash(str(tweets))
        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_timeout:
                return cached_result

        if not tweets:
            return {
                'summary': "Aucun tweet disponible pour la période.",
                'hashtags': [],
                'engagement': 0.0,
                'themes': []
            }

        # Préparation des données
        texts = []
        hashtags = []
        total_engagement = 0
        tweet_count = 0

        for tweet in tweets:
            texts.append(tweet['text'])
            hashtags.extend(tweet['hashtags'])
            
            # Calcul de l'engagement en prenant en compte les différents formats possibles
            metrics = tweet['metrics']
            likes = metrics.get('like', metrics.get('like_count', 0))
            retweets = metrics.get('retweet', metrics.get('retweet_count', 0))
            replies = metrics.get('reply', metrics.get('reply_count', 0))
            
            tweet_engagement = likes + retweets + replies
            total_engagement += tweet_engagement
            tweet_count += 1

        # Calcul de l'engagement moyen
        avg_engagement = total_engagement / max(tweet_count, 1)

        # Analyse des hashtags les plus fréquents
        hashtag_counter = Counter(hashtags)
        top_hashtags = [tag for tag, _ in hashtag_counter.most_common(5)]

        # Extraction des thèmes
        themes = self._extract_themes(tweets)

        # Génération du résumé
        if len(texts) == 1:
            summary = texts[0]
        else:
            # Tokenisation des phrases
            all_sentences = []
            for text in texts:
                sentences = sent_tokenize(text)
                all_sentences.extend(sentences)

            if not all_sentences:
                summary = "Pas de contenu textuel disponible dans les tweets."
            else:
                # Sélection des phrases les plus pertinentes
                summary = " ".join(all_sentences[:3])

        result = {
            'summary': summary,
            'hashtags': top_hashtags,
            'engagement': round(avg_engagement, 2),
            'themes': themes
        }

        # Mise en cache du résultat
        self._cache[cache_key] = (result, time.time())

        return result

    def _generate_summary(self, tweets: List[Dict[str, Any]], top_hashtags: List[str], avg_engagement: float) -> str:
        """Génère un résumé intelligent des tweets."""
        if len(tweets) < config.MIN_TWEETS_FOR_SUMMARY:
            return "Pas assez de tweets récents pour générer un résumé pertinent."

        # Analyse des thèmes principaux
        themes = self._extract_themes(tweets)
        
        # Construction du résumé
        summary_parts = [
            f"📊 Analyse des {len(tweets)} derniers tweets :",
            f"🎯 Thèmes principaux : {', '.join(themes[:3])}",
            f"💫 Engagement moyen : {avg_engagement:.1f} interactions par tweet"
        ]

        if top_hashtags:
            summary_parts.append(f"🏷️ Hashtags populaires : #{', #'.join(top_hashtags)}")

        return "\n".join(summary_parts)

    def _extract_themes(self, tweets: List[Dict[str, Any]]) -> List[str]:
        """Extrait les thèmes principaux des tweets."""
        themes = set()
        keywords = {
            'Bitcoin': ['bitcoin', 'btc', 'satoshi'],
            'Ethereum': ['ethereum', 'eth', 'vitalik'],
            'DeFi': ['defi', 'yield', 'liquidity', 'swap'],
            'NFT': ['nft', 'opensea', 'collection'],
            'Regulation': ['sec', 'regulation', 'compliance']
        }

        for tweet in tweets:
            text = tweet['text'].lower()
            for theme, words in keywords.items():
                if any(word in text for word in words):
                    themes.add(theme)

        return list(themes)

    def summarize_all_accounts(self, all_tweets: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """Génère des résumés pour tous les comptes."""
        summaries = {}
        for account, tweets in all_tweets.items():
            logger.info(f"Génération du résumé pour {account}")
            summaries[account] = self.analyze_tweets(tweets)
        return summaries 