import json
from datetime import datetime
from twitter_fetcher import TwitterFetcher
from summarizer import TweetSummarizer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_summaries(summaries: dict, filename: str = None):
    """Sauvegarde les résumés dans un fichier JSON."""
    if filename is None:
        filename = f"crypto_summaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)
    logger.info(f"Résumés sauvegardés dans {filename}")

def display_summaries(summaries: dict):
    """Affiche les résumés dans la console."""
    print("\n=== RÉSUMÉ DE LA VEILLE CRYPTO ===\n")
    for account, data in summaries.items():
        print(f"\n📱 @{account}")
        print("-" * 50)
        print(data['summary'])
        if data['hashtags']:
            print(f"\n🏷️ Hashtags populaires : #{', #'.join(data['hashtags'])}")
        print(f"💫 Engagement moyen : {data['engagement']:.1f}")
        print("-" * 50)

def main():
    try:
        # Initialisation des composants
        fetcher = TwitterFetcher()
        summarizer = TweetSummarizer()

        # Récupération des tweets
        logger.info("Début de la récupération des tweets...")
        all_tweets = fetcher.fetch_all_accounts()
        logger.info(f"Récupération terminée pour {len(all_tweets)} comptes")

        # Génération des résumés
        logger.info("Génération des résumés...")
        summaries = summarizer.summarize_all_accounts(all_tweets)

        # Affichage et sauvegarde des résultats
        display_summaries(summaries)
        save_summaries(summaries)

    except Exception as e:
        logger.error(f"Une erreur est survenue : {str(e)}")
        raise

if __name__ == "__main__":
    main() 