import json
import argparse
from datetime import datetime
from twitter_fetcher import TwitterFetcher
from market_data_fetcher import MarketDataFetcher
from external_sources_fetcher import ExternalSourcesFetcher
from summarizer import TweetSummarizer
import logging
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_data(tweet_summaries: Dict[str, Dict[str, Any]], market_data: Dict[str, Any], external_data: Dict[str, Any]):
    """Sauvegarde les données dans un fichier JSON."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crypto_data_{timestamp}.json"
        
        data = {
            'timestamp': timestamp,
            'tweet_summaries': tweet_summaries,
            'market_data': market_data,
            'external_data': external_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Données sauvegardées dans {filename}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des données : {str(e)}")

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

def display_market_data(market_data: dict):
    """Affiche les données de marché dans la console."""
    print("\n=== DONNÉES DE MARCHÉ ===\n")
    
    # Affichage des prix
    if 'prices' in market_data:
        print("💰 Prix des Cryptos :")
        for crypto, price in market_data['prices'].get('prices', {}).items():
            change = market_data['prices'].get('changes_24h', {}).get(crypto, 0)
            print(f"  {crypto.upper()}: ${price:,.2f} ({change:+.2f}%)")
    
    # Affichage des alertes de baleines
    if 'whale_alerts' in market_data and market_data['whale_alerts']:
        print("\n🐋 Dernières Alertes de Baleines :")
        for alert in market_data['whale_alerts'][:3]:  # Afficher les 3 dernières alertes
            print(f"  {alert['currency']}: {alert['amount_usd']:,.2f} USD")
    
    # Affichage des métriques de sentiment
    if 'sentiment' in market_data:
        print("\n📊 Métriques de Sentiment :")
        if 'metrics' in market_data['sentiment']:
            metrics = market_data['sentiment']['metrics']
            if 'fear_and_greed' in metrics:
                print(f"  Fear & Greed Index: {metrics['fear_and_greed']}")
            if 'nvt' in metrics:
                print(f"  NVT Ratio: {metrics['nvt']}")

def display_external_sources(external_data):
    """Affiche les données des sources externes."""
    print("\n=== SOURCES EXTERNES ===\n")
    
    # Affichage des actualités réglementaires
    if 'regulatory_news' in external_data:
        print("⚖️ Actualités Réglementaires :")
        for news in external_data['regulatory_news'][:5]:
            print(f"  {news}")
    
    # Affichage des tendances Google
    if 'google_trends' in external_data:
        print("\n📈 Tendances Google :")
        for keyword, data in external_data['google_trends'].items():
            if isinstance(data, dict) and 'data' in data:
                try:
                    trend_data = data['data'].get(keyword, [])
                    if trend_data:
                        latest_value = trend_data[-1]
                        print(f"  {keyword.upper()}: {latest_value:.0f}")
                except (IndexError, AttributeError) as e:
                    logger.warning(f"Erreur lors de l'affichage des tendances pour {keyword}: {str(e)}")

def main():
    """Fonction principale."""
    try:
        parser = argparse.ArgumentParser(description='Veille Crypto - Récupération et analyse des tweets crypto')
        parser.add_argument('--market-only', action='store_true', help='Récupérer uniquement les données de marché')
        args = parser.parse_args()
        
        # Initialisation des composants
        tweet_fetcher = TwitterFetcher()
        summarizer = TweetSummarizer()
        market_fetcher = MarketDataFetcher()
        external_fetcher = ExternalSourcesFetcher()
        
        # Récupération des données de marché
        logger.info("Récupération des données de marché...")
        market_data = market_fetcher.fetch_all_market_data()
        display_market_data(market_data)
        
        if not args.market_only:
            # Récupération des tweets
            logger.info("Début de la récupération des tweets...")
            all_tweets = tweet_fetcher.fetch_all_accounts()
            logger.info(f"Récupération terminée pour {len(all_tweets)} comptes")
            
            # Génération des résumés
            logger.info("Génération des résumés...")
            summaries = summarizer.summarize_all_accounts(all_tweets)
            
            # Affichage des résumés
            print("\n=== RÉSUMÉ DE LA VEILLE CRYPTO ===\n")
            for account, summary in summaries.items():
                print(f"\n📱 @{account}")
                print("-" * 50)
                print(f"📊 Analyse des {len(all_tweets.get(account, []))} derniers tweets :")
                print(f"🎯 Thèmes principaux : {', '.join(summary.get('themes', []))}")
                print(f"💫 Engagement moyen : {summary.get('engagement', 0.0)} interactions par tweet")
                if summary.get('hashtags'):
                    print(f"🏷️ Hashtags populaires : {' '.join(summary['hashtags'])}")
                print("\n" + summary['summary'])
                print("-" * 50)
        
        # Récupération des sources externes
        logger.info("Récupération des sources externes...")
        external_data = external_fetcher.fetch_all_sources()
        display_external_sources(external_data)
        
        # Sauvegarde des données
        if not args.market_only:
            save_data(summaries, market_data, external_data)
        else:
            save_data({}, market_data, external_data)
            
    except Exception as e:
        logger.error(f"Une erreur est survenue : {str(e)}")
        raise

if __name__ == "__main__":
    main() 