import os
import json
import argparse
from datetime import datetime
from twitter_fetcher import TwitterFetcher
from rss_fetcher import RSSFetcher
from market_data_fetcher import MarketDataFetcher
from external_sources_fetcher import ExternalSourcesFetcher
from summarizer import TweetSummarizer
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def display_market_data(market_data: Dict[str, Any]):
    """Affiche les données de marché de manière formatée."""
    print("\n=== DONNÉES DE MARCHÉ ===\n")
    
    # Affichage des prix des cryptos
    if 'prices' in market_data and 'prices' in market_data['prices']:
        print("💰 Prix des Cryptos :")
        for crypto, price in market_data['prices']['prices'].items():
            change = market_data['prices']['changes_24h'].get(crypto, 0)
            print(f"  {crypto.upper()}: ${price:,.2f} ({change:+.2f}%)")
    
    # Affichage des alertes de baleines
    if 'whale_alerts' in market_data and market_data['whale_alerts']:
        print("\n🐋 Alertes de Baleines :")
        for alert in market_data['whale_alerts'][:5]:  # Limite aux 5 dernières alertes
            print(f"  {alert['amount']} {alert['symbol']} - {alert['type']}")
    
    # Affichage des métriques de sentiment
    if 'sentiment' in market_data and 'metrics' in market_data['sentiment']:
        print("\n📊 Métriques de Sentiment :")
        for metric, value in market_data['sentiment']['metrics'].items():
            print(f"  {metric}: {value}")

def display_rss_data(rss_data: List[Dict[str, Any]]):
    """Affiche les données RSS de manière formatée."""
    print("\n=== ACTUALITÉS CRYPTO ===\n")
    
    if not rss_data:
        print("Aucune actualité disponible")
        return
    
    for entry in rss_data[:10]:  # Limite aux 10 dernières actualités
        print(f"📰 {entry['title']}")
        print(f"   {entry['summary'][:200]}...")  # Limite le résumé à 200 caractères
        print(f"   🔗 {entry['link']}")
        print(f"   📅 {entry['published']}")
        print("-" * 80)

def save_data(tweets: Dict[str, Any], market_data: Dict[str, Any], rss_data: List[Dict[str, Any]], filename: str = None):
    """Sauvegarde les données dans un fichier JSON."""
    if filename is None:
        filename = f"crypto_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    data = {
        'tweets': tweets,
        'market_data': market_data,
        'rss_data': rss_data,
        'timestamp': datetime.now().isoformat()
    }
    
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
        # Chargement des variables d'environnement
        load_dotenv()
        
        # Récupération des données de marché
        logger.info("Récupération des données de marché...")
        market_fetcher = MarketDataFetcher()
        market_data = market_fetcher.fetch_all_market_data()
        display_market_data(market_data)
        
        # Récupération des flux RSS
        logger.info("Récupération des flux RSS...")
        rss_fetcher = RSSFetcher()
        rss_data = rss_fetcher.fetch_feeds()
        display_rss_data(rss_data)
        
        # Récupération des tweets
        logger.info("Début de la récupération des tweets...")
        twitter_fetcher = TwitterFetcher()
        tweets = twitter_fetcher.fetch_all_accounts()
        
        # Génération des résumés
        logger.info("Génération des résumés...")
        summarizer = TweetSummarizer()
        summaries = summarizer.analyze_tweets(tweets)
        
        # Sauvegarde des données
        save_data(tweets, market_data, rss_data)
        
        logger.info("Traitement terminé avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution : {str(e)}")
        raise

if __name__ == "__main__":
    main() 