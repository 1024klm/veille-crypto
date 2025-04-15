import unittest
from summarizer import TweetSummarizer
from typing import List, Dict, Any
from datetime import datetime, timedelta

class TestTweetSummarizer(unittest.TestCase):
    def setUp(self):
        self.summarizer = TweetSummarizer()
        
    def test_empty_tweets(self):
        """Test avec une liste de tweets vide."""
        result = self.summarizer.analyze_tweets([])
        self.assertEqual(result['summary'], "Aucun tweet disponible pour la période.")
        self.assertEqual(result['hashtags'], [])
        self.assertEqual(result['engagement'], 0.0)
        self.assertEqual(result['themes'], [])

    def test_single_tweet(self):
        """Test de la génération de résumé pour un seul tweet."""
        tweets = [{
            'text': 'Test tweet #crypto',
            'date': '2024-03-20T10:00:00Z',
            'metrics': {
                'like': 100,
                'retweet': 50,
                'reply': 30
            },
            'hashtags': ['crypto']
        }]
        
        result = self.summarizer.analyze_tweets(tweets)
        self.assertIsNotNone(result)
        self.assertIn('Test tweet', result['summary'])
        self.assertIn('crypto', result['hashtags'])
        self.assertEqual(result['engagement'], 180.0)

    def test_multiple_tweets(self):
        """Test de la génération de résumé pour plusieurs tweets."""
        tweets = [
            {
                'text': 'Premier tweet #crypto',
                'date': '2024-03-20T10:00:00Z',
                'metrics': {
                    'like': 100,
                    'retweet': 50,
                    'reply': 30
                },
                'hashtags': ['crypto']
            },
            {
                'text': 'Deuxième tweet #bitcoin',
                'date': '2024-03-20T11:00:00Z',
                'metrics': {
                    'like': 200,
                    'retweet': 100,
                    'reply': 60
                },
                'hashtags': ['bitcoin']
            }
        ]
        
        result = self.summarizer.analyze_tweets(tweets)
        self.assertIsNotNone(result)
        self.assertIn('Premier tweet', result['summary'])
        self.assertIn('Deuxième tweet', result['summary'])
        self.assertTrue(all(tag in result['hashtags'] for tag in ['crypto', 'bitcoin']))
        self.assertEqual(result['engagement'], 270.0)

    def test_no_tweets(self):
        """Test de la génération de résumé sans tweets."""
        result = self.summarizer.analyze_tweets([])
        self.assertIsNotNone(result)
        self.assertEqual(result['summary'], "Aucun tweet disponible pour la période.")
        self.assertEqual(result['hashtags'], [])
        self.assertEqual(result['engagement'], 0.0)
        self.assertEqual(result['themes'], [])

    def test_tweets_with_different_metric_formats(self):
        """Test de la génération de résumé avec différents formats de métriques."""
        tweets = [
            {
                'text': 'Tweet avec like_count #crypto',
                'date': '2024-03-20T10:00:00Z',
                'metrics': {
                    'like_count': 100,
                    'retweet_count': 50,
                    'reply_count': 30
                },
                'hashtags': ['crypto']
            },
            {
                'text': 'Tweet avec like #bitcoin',
                'date': '2024-03-20T11:00:00Z',
                'metrics': {
                    'like': 200,
                    'retweet': 100,
                    'reply': 60
                },
                'hashtags': ['bitcoin']
            }
        ]
        
        result = self.summarizer.analyze_tweets(tweets)
        self.assertIsNotNone(result)
        self.assertIn('Tweet avec like_count', result['summary'])
        self.assertIn('Tweet avec like', result['summary'])
        self.assertTrue(all(tag in result['hashtags'] for tag in ['crypto', 'bitcoin']))
        self.assertEqual(result['engagement'], 270.0)

    def test_cache_functionality(self):
        """Test du fonctionnement du cache."""
        tweets = [{
            'text': 'Test tweet #Test',
            'date': '2024-03-20T10:00:00Z',
            'metrics': {'like': 10},
            'hashtags': ['Test']
        }]
        
        # Premier appel
        result1 = self.summarizer.analyze_tweets(tweets)
        
        # Deuxième appel (devrait utiliser le cache)
        result2 = self.summarizer.analyze_tweets(tweets)
        
        self.assertEqual(result1, result2)

    def test_theme_extraction(self):
        """Test de l'extraction des thèmes."""
        tweets = [
            {
                'text': 'Bitcoin atteint un nouveau record ! #BTC',
                'date': '2024-03-20T10:00:00Z',
                'metrics': {'like': 100, 'retweet': 50},
                'hashtags': ['BTC']
            },
            {
                'text': 'Nouveau protocole DeFi sur Ethereum #ETH',
                'date': '2024-03-20T11:00:00Z',
                'metrics': {'like': 80, 'retweet': 30},
                'hashtags': ['ETH']
            }
        ]
        
        result = self.summarizer.analyze_tweets(tweets)
        self.assertIn('Bitcoin', result['themes'])
        self.assertIn('Ethereum', result['themes'])
        self.assertIn('DeFi', result['themes'])

if __name__ == '__main__':
    unittest.main() 