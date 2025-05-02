import pytest
from src.external_sources_fetcher import ExternalSourcesFetcher
from datetime import datetime, timezone

def test_get_news_articles():
    """Test la récupération des articles de news."""
    fetcher = ExternalSourcesFetcher()
    articles = fetcher.get_news_articles()
    
    assert isinstance(articles, list)
    
    if articles:  # Si des articles ont été récupérés
        article = articles[0]
        assert isinstance(article, dict)
        assert 'source' in article
        assert 'title' in article
        assert 'link' in article
        assert 'published' in article
        assert 'summary' in article
        
        assert article['source'] in ['coindesk', 'cointelegraph', 'cryptonews']

def test_get_reddit_posts():
    """Test la récupération des posts Reddit."""
    fetcher = ExternalSourcesFetcher()
    posts = fetcher.get_reddit_posts()
    
    assert isinstance(posts, list)
    
    if posts:  # Si des posts ont été récupérés
        post = posts[0]
        assert isinstance(post, dict)
        assert 'source' in post
        assert 'subreddit' in post
        assert 'title' in post
        assert 'url' in post
        assert 'score' in post
        assert 'num_comments' in post
        assert 'created_utc' in post
        
        assert post['source'] == 'reddit'
        assert post['subreddit'] in ['cryptocurrency', 'bitcoin', 'ethereum']

def test_fetch_all_external_data():
    """Test la récupération de toutes les données externes."""
    fetcher = ExternalSourcesFetcher()
    data = fetcher.fetch_all_external_data()
    
    assert isinstance(data, dict)
    assert 'timestamp' in data
    assert 'news' in data
    assert 'reddit' in data
    
    # Vérification du format de la date
    try:
        datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("Le format de la date n'est pas valide") 