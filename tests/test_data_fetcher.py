import unittest
from unittest.mock import patch, MagicMock
from twitter_fetcher import TwitterFetcher
from rss_fetcher import RSSFetcher
import os
from datetime import datetime, timedelta

class TestDataFetcher(unittest.TestCase):
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.twitter_fetcher = TwitterFetcher()
        self.rss_fetcher = RSSFetcher()
        
        # Configuration des variables d'environnement pour les tests
        os.environ['TWITTER_USERNAME'] = 'test_user'
        os.environ['TWITTER_PASSWORD'] = 'test_pass'
        
    def tearDown(self):
        """Nettoyage après les tests."""
        if hasattr(self, 'twitter_fetcher') and self.twitter_fetcher.driver:
            self.twitter_fetcher.driver.quit()

    @patch('twitter_fetcher.webdriver.Chrome')
    def test_fetch_twitter_data(self, mock_chrome):
        """Test de la récupération des données Twitter."""
        # Configuration du mock
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock des éléments de tweet
        mock_tweet = MagicMock()
        mock_tweet.find_element.return_value.text = "Test tweet content"
        mock_tweet.find_element.return_value.get_attribute.return_value = datetime.now().isoformat()
        
        # Mock des métriques
        mock_metrics = {
            'reply': '10',
            'retweet': '20',
            'like': '30'
        }
        
        def mock_find_elements(by, value):
            if 'metrics' in value:
                return [MagicMock(text=v) for v in mock_metrics.values()]
            return [mock_tweet]
            
        mock_driver.find_elements.side_effect = mock_find_elements
        
        # Configuration du fetcher
        self.twitter_fetcher.driver = mock_driver
        
        # Test de la récupération des tweets
        tweets = self.twitter_fetcher.fetch_account_tweets("test_account", max_tweets=1)
        
        # Vérifications
        self.assertIsInstance(tweets, list)
        self.assertEqual(len(tweets), 1)
        self.assertIn('text', tweets[0])
        self.assertIn('date', tweets[0])
        self.assertIn('metrics', tweets[0])

    @patch('feedparser.parse')
    def test_fetch_rss_data(self, mock_parse):
        """Test de la récupération des données RSS."""
        # Configuration du mock pour simuler plusieurs entrées par flux
        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                'title': f'Test RSS Entry {i}',
                'link': f'http://test{i}.com',
                'published': datetime.now().isoformat(),
                'summary': f'Test RSS content {i}'
            } for i in range(4)  # 4 entrées par flux
        ]
        mock_parse.return_value = mock_feed
        
        # Test de la récupération des flux RSS
        feeds = self.rss_fetcher.fetch_feeds()
        
        # Vérifications
        self.assertIsInstance(feeds, list)
        self.assertTrue(len(feeds) > 0)  # Nous devrions avoir au moins une entrée
        for feed in feeds:
            self.assertIn('title', feed)
            self.assertIn('link', feed)
            self.assertIn('published', feed)
            self.assertIn('summary', feed)
            self.assertIn('source', feed)
            
        # Vérification que nous avons des entrées de chaque source
        sources = set(feed['source'] for feed in feeds)
        self.assertEqual(len(sources), 4)  # Nous devrions avoir des entrées des 4 sources

    def test_data_integration(self):
        """Test d'intégration des données Twitter et RSS."""
        # Test de la récupération combinée
        with patch('twitter_fetcher.TwitterFetcher.fetch_account_tweets') as mock_twitter, \
             patch('rss_fetcher.RSSFetcher.fetch_feeds') as mock_rss:
            
            # Configuration des mocks
            mock_twitter.return_value = [{'text': 'Twitter test', 'date': datetime.now().isoformat()}]
            mock_rss.return_value = [{'title': 'RSS test', 'published': datetime.now().isoformat()}]
            
            # Récupération des données
            twitter_data = self.twitter_fetcher.fetch_account_tweets("test_account")
            rss_data = self.rss_fetcher.fetch_feeds()
            
            # Vérifications
            self.assertIsInstance(twitter_data, list)
            self.assertIsInstance(rss_data, list)
            self.assertTrue(len(twitter_data) > 0)
            self.assertTrue(len(rss_data) > 0)

if __name__ == '__main__':
    unittest.main() 