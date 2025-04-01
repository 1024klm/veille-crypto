from typing import List, Dict, Any
import nltk
from collections import Counter
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TweetSummarizer:
    def __init__(self):
        # Téléchargement des ressources NLTK nécessaires
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

    def analyze_tweets(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse un ensemble de tweets pour en extraire les informations clés."""
        if not tweets:
            return {
                'summary': "Aucun tweet récent trouvé.",
                'hashtags': [],
                'engagement': 0
            }

        # Extraction des hashtags
        all_hashtags = []
        for tweet in tweets:
            all_hashtags.extend(tweet.get('hashtags', []))
        
        # Calcul des hashtags les plus fréquents
        hashtag_counter = Counter(all_hashtags)
        top_hashtags = [tag for tag, _ in hashtag_counter.most_common(config.MAX_HASHTAGS)]

        # Calcul de l'engagement moyen
        total_engagement = sum(
            tweet['metrics']['like_count'] + 
            tweet['metrics']['retweet_count'] + 
            tweet['metrics']['reply_count']
            for tweet in tweets
        )
        avg_engagement = total_engagement / len(tweets) if tweets else 0

        # Génération du résumé
        summary = self._generate_summary(tweets, top_hashtags, avg_engagement)

        return {
            'summary': summary,
            'hashtags': top_hashtags,
            'engagement': round(avg_engagement, 2)
        }

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
        # Mots-clés crypto courants
        crypto_keywords = {
            'bitcoin': 'Bitcoin',
            'btc': 'Bitcoin',
            'eth': 'Ethereum',
            'ethereum': 'Ethereum',
            'defi': 'DeFi',
            'nft': 'NFT',
            'web3': 'Web3',
            'blockchain': 'Blockchain',
            'mining': 'Mining',
            'trading': 'Trading',
            'altcoin': 'Altcoins',
            'stablecoin': 'Stablecoins'
        }

        themes = []
        for tweet in tweets:
            text = tweet['text'].lower()
            for keyword, theme in crypto_keywords.items():
                if keyword in text and theme not in themes:
                    themes.append(theme)

        return themes[:5]  # Limite à 5 thèmes principaux

    def summarize_all_accounts(self, all_tweets: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """Génère des résumés pour tous les comptes."""
        summaries = {}
        for account, tweets in all_tweets.items():
            logger.info(f"Génération du résumé pour {account}")
            summaries[account] = self.analyze_tweets(tweets)
        return summaries 