import json
import argparse
from datetime import datetime
from twitter_fetcher import TwitterFetcher
from market_data_fetcher import MarketDataFetcher
from external_sources_fetcher import ExternalSourcesFetcher
from summarizer import TweetSummarizer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_data(data: dict, filename: str = None):
    """Sauvegarde les données dans un fichier JSON."""
    if filename is None:
        filename = f"crypto_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Données sauvegardées dans {filename}")

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

def display_external_sources(external_data: dict):
    """Affiche les données des sources externes dans la console."""
    print("\n=== SOURCES EXTERNES ===\n")
    
    # Affichage des actualités réglementaires
    if external_data.get('regulatory'):
        print("⚖️ Actualités Réglementaires :")
        for item in external_data['regulatory'][:3]:  # Afficher les 3 dernières actualités
            print(f"  [{item['source'].upper()}] {item['title']}")
    
    # Affichage des actualités des exchanges
    if external_data.get('exchanges'):
        print("\n🏦 Actualités des Exchanges :")
        for item in external_data['exchanges'][:3]:
            print(f"  [{item['source'].upper()}] {item['title']}")
    
    # Affichage des tendances Google
    if external_data.get('trends'):
        trends = external_data['trends']
        if 'data' in trends and trends['data']:
            print("\n📈 Tendances Google :")
            for keyword in trends['keywords']:
                if keyword in trends['data']:
                    print(f"  {keyword.upper()}: {trends['data'][keyword].iloc[-1]:.0f}")
    
    # Affichage des actualités CryptoPanic
    if external_data.get('news'):
        print("\n📰 Actualités CryptoPanic :")
        for item in external_data['news'][:3]:
            sentiment_emoji = "🟢" if item['sentiment'] == 'positive' else "🔴" if item['sentiment'] == 'negative' else "⚪"
            print(f"  {sentiment_emoji} {item['title']}")

def main():
    parser = argparse.ArgumentParser(description='Veille Crypto Twitter et Marché')
    parser.add_argument('--market-only', action='store_true', help='Récupérer uniquement les données de marché')
    parser.add_argument('--external-only', action='store_true', help='Récupérer uniquement les sources externes')
    args = parser.parse_args()

    try:
        all_data = {}
        
        if not args.external_only:
            if not args.market_only:
                # Récupération des tweets
                logger.info("Début de la récupération des tweets...")
                fetcher = TwitterFetcher()
                all_tweets = fetcher.fetch_all_accounts()
                logger.info(f"Récupération terminée pour {len(all_tweets)} comptes")

                # Génération des résumés
                logger.info("Génération des résumés...")
                summarizer = TweetSummarizer()
                summaries = summarizer.summarize_all_accounts(all_tweets)
                all_data['tweets'] = summaries

            # Récupération des données de marché
            logger.info("Récupération des données de marché...")
            market_fetcher = MarketDataFetcher()
            market_data = market_fetcher.fetch_all_market_data()
            all_data['market'] = market_data

        # Récupération des sources externes
        if not args.market_only:
            logger.info("Récupération des sources externes...")
            external_fetcher = ExternalSourcesFetcher()
            external_data = external_fetcher.fetch_all_sources()
            all_data['external_sources'] = external_data

        # Affichage et sauvegarde des résultats
        if not args.external_only:
            if not args.market_only:
                display_summaries(summaries)
            display_market_data(market_data)
        
        if not args.market_only:
            display_external_sources(external_data)
            
        save_data(all_data)

    except Exception as e:
        logger.error(f"Une erreur est survenue : {str(e)}")
        raise

if __name__ == "__main__":
    main() 