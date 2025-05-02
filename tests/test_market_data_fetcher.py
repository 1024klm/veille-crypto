import pytest
from src.market_data_fetcher import MarketDataFetcher
from datetime import datetime, timezone

def test_get_top_crypto_prices():
    """Test la récupération des prix des cryptos."""
    fetcher = MarketDataFetcher()
    data = fetcher.get_top_crypto_prices()
    
    assert isinstance(data, dict)
    assert 'source' in data
    assert 'timestamp' in data
    assert 'prices' in data
    assert 'market_caps' in data
    assert 'changes_24h' in data
    
    # Vérification des cryptos principales
    expected_cryptos = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']
    for crypto in expected_cryptos:
        assert crypto in data['prices']
        assert crypto in data['market_caps']
        assert crypto in data['changes_24h']

def test_get_sentiment_metrics():
    """Test la récupération des métriques de sentiment."""
    fetcher = MarketDataFetcher()
    data = fetcher.get_sentiment_metrics()
    
    assert isinstance(data, dict)
    assert 'source' in data
    assert 'timestamp' in data
    assert 'metrics' in data
    
    metrics = data['metrics']
    assert 'bullish_count' in metrics
    assert 'bearish_count' in metrics
    assert 'total_entries' in metrics
    assert 'sentiment_score' in metrics
    
    assert isinstance(metrics['bullish_count'], int)
    assert isinstance(metrics['bearish_count'], int)
    assert isinstance(metrics['total_entries'], int)
    assert isinstance(metrics['sentiment_score'], float)
    assert -1 <= metrics['sentiment_score'] <= 1

def test_fetch_all_market_data():
    """Test la récupération de toutes les données de marché."""
    fetcher = MarketDataFetcher()
    data = fetcher.fetch_all_market_data()
    
    assert isinstance(data, dict)
    assert 'timestamp' in data
    assert 'prices' in data
    assert 'sentiment' in data
    
    # Vérification du format de la date
    try:
        datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("Le format de la date n'est pas valide") 