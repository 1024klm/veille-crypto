import os
import json
import argparse
from datetime import datetime, timezone
from twitter_fetcher import TwitterFetcher
from rss_fetcher import RSSFetcher
from market_data_fetcher import MarketDataFetcher
from external_sources_fetcher import ExternalSourcesFetcher
from summarizer import TweetSummarizer
from notifier import CryptoNotifier
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
import config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    
    # Affichage des cryptos tendances
    if 'trending' in market_data and market_data['trending']:
        print("\n🔥 Cryptos Tendances :")
        for coin in market_data['trending'][:5]:
            print(f"  • {coin.get('name', 'N/A')} ({coin.get('symbol', 'N/A')}) - Rang: {coin.get('market_cap_rank', 'N/A')}")
    
    # Affichage des alertes de baleines
    if 'whale_alerts' in market_data and market_data['whale_alerts']:
        print("\n🐋 Alertes de Baleines :")
        for alert in market_data['whale_alerts'][:5]:
            if 'amount' in alert and 'symbol' in alert:
                print(f"  • {alert['amount']} {alert['symbol']} - {alert.get('type', 'unknown')}")
    
    # Affichage des données globales du marché
    if 'market_cap' in market_data and market_data['market_cap']:
        print("\n🌍 Données Globales du Marché :")
        mc_data = market_data['market_cap']
        if mc_data.get('total_market_cap'):
            print(f"  Cap. totale: ${mc_data['total_market_cap']:,.0f}")
        if mc_data.get('total_volume'):
            print(f"  Volume 24h: ${mc_data['total_volume']:,.0f}")
        if mc_data.get('active_cryptocurrencies'):
            print(f"  Cryptos actives: {mc_data['active_cryptocurrencies']:,}")
    
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

def save_data(data: dict, filename: str):
    """Sauvegarde les données dans un fichier JSON."""
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        filepath = os.path.join(config.DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Données sauvegardées dans {filepath}")
        
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

def display_external_sources(external_data):
    """Affiche les données des sources externes."""
    print("\n=== SOURCES EXTERNES ===\n")
    
    # Affichage des actualités réglementaires
    if 'regulatory' in external_data:
        print("⚖️ Actualités Réglementaires :")
        for news in external_data['regulatory'][:3]:
            print(f"  📰 {news.get('title', 'Sans titre')}")
            print(f"     {news.get('summary', '')[:100]}...")
    
    # Affichage des médias spécialisés
    if 'media' in external_data:
        print("\n📰 Médias Crypto :")
        for news in external_data['media'][:5]:
            print(f"  • {news.get('title', 'Sans titre')} ({news.get('source', '')})")
    
    # Affichage des newsletters
    if 'newsletters' in external_data:
        print("\n✉️ Newsletters :")
        for item in external_data['newsletters'][:3]:
            print(f"  • {item.get('title', 'Sans titre')}")
    
    # Affichage des analyses on-chain
    if 'analytics' in external_data:
        print("\n📊 Analyses On-chain :")
        for analysis in external_data['analytics'][:3]:
            print(f"  • {analysis.get('title', 'Sans titre')} ({analysis.get('source', '')})")
    
    # Affichage des actualités françaises
    if 'french' in external_data:
        print("\n🇫🇷 Actualités Françaises :")
        for news in external_data['french'][:3]:
            print(f"  • {news.get('title', 'Sans titre')} ({news.get('source', '')})")
    
    # Affichage des tendances Google
    if 'trends' in external_data and isinstance(external_data['trends'], dict):
        print("\n📈 Tendances Google :")
        trends_data = external_data['trends'].get('data', {})
        for keyword in external_data['trends'].get('keywords', []):
            if keyword in trends_data:
                try:
                    values = list(trends_data[keyword].values())
                    if values:
                        latest_value = values[-1]
                        print(f"  {keyword.upper()}: {latest_value}")
                except Exception as e:
                    logger.warning(f"Erreur tendances {keyword}: {str(e)}")

def parse_args():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(description='Veille Crypto - Récupération des données')
    parser.add_argument('--skip-twitter', action='store_true', help='Désactive la récupération des tweets')
    parser.add_argument('--skip-market', action='store_true', help='Désactive la récupération des données de marché')
    parser.add_argument('--skip-external', action='store_true', help='Désactive la récupération des sources externes')
    parser.add_argument('--free-only', action='store_true', help='Utilise uniquement les sources gratuites')
    return parser.parse_args()

def main():
    """Point d'entrée principal."""
    # Chargement des variables d'environnement
    load_dotenv()
    
    # Parse des arguments
    args = parse_args()
    
    # Gestion du flag --free-only
    if args.free_only:
        args.skip_twitter = True  # ChromeDriver gratuit mais facultatif
        args.skip_market = False  # CoinGecko OK
        args.skip_external = False  # RSS OK
    
    # Initialisation des fetchers
    twitter_fetcher = None
    market_fetcher = None
    external_fetcher = None
    
    if not args.skip_twitter:
        try:
            twitter_fetcher = TwitterFetcher()
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de TwitterFetcher : {str(e)}")
            args.skip_twitter = True
    
    if not args.skip_market:
        try:
            market_fetcher = MarketDataFetcher()
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de MarketDataFetcher : {str(e)}")
            args.skip_market = True
    
    if not args.skip_external:
        try:
            external_fetcher = ExternalSourcesFetcher()
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de ExternalSourcesFetcher : {str(e)}")
            args.skip_external = True
    
    # Récupération des données
    all_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'twitter': {},
        'market': {},
        'external': {}
    }
    
    # Récupération des tweets
    if not args.skip_twitter and twitter_fetcher:
        try:
            all_data['twitter'] = twitter_fetcher.fetch_all_accounts()
            save_data(all_data['twitter'], 'twitter_data.json')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tweets : {str(e)}")
    
    # Récupération des données de marché
    if not args.skip_market and market_fetcher:
        try:
            all_data['market'] = market_fetcher.fetch_all_market_data()
            save_data(all_data['market'], 'market_data.json')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de marché : {str(e)}")
    
    # Récupération des sources externes
    if not args.skip_external and external_fetcher:
        try:
            all_data['external'] = external_fetcher.fetch_all_sources()
            save_data(all_data['external'], 'external_data.json')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sources externes : {str(e)}")
    
    # Sauvegarde des données complètes
    save_data(all_data, 'all_data.json')
    
    # Vérification des alertes et notifications
    try:
        notifier = CryptoNotifier()
        notifier.check_and_notify(all_data)
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des notifications : {str(e)}")
    
    # Affichage des données (optionnel)
    if not args.skip_market and 'market' in all_data:
        display_market_data(all_data['market'])
    
    if not args.skip_external and 'external' in all_data:
        display_external_sources(all_data['external'])
    
    # Nettoyage
    if twitter_fetcher:
        try:
            twitter_fetcher.cleanup()
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage de TwitterFetcher : {str(e)}")

if __name__ == "__main__":
    main() 