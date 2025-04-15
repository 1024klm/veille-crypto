import unittest
from unittest.mock import MagicMock, patch
from twitter_fetcher import TwitterFetcher
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

class TestTwitterFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = TwitterFetcher()
        
    def tearDown(self):
        if self.fetcher.driver:
            self.fetcher.driver.quit()

    @patch('twitter_fetcher.webdriver.Chrome')
    def test_setup_driver(self, mock_chrome):
        """Test de l'initialisation du driver."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Réinitialisation du driver pour le test
        self.fetcher.driver = None
        self.fetcher.setup_driver()
        
        # Vérification que le driver a été initialisé
        self.assertIsNotNone(self.fetcher.driver)
        mock_chrome.assert_called_once()

    @patch('twitter_fetcher.WebDriverWait')
    @patch('twitter_fetcher.webdriver.Chrome')
    def test_login(self, mock_chrome, mock_wait):
        """Test de la connexion à Twitter."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        mock_element = MagicMock()
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = mock_element
        
        # Configuration du mock pour find_element
        mock_next_button = MagicMock()
        mock_driver.find_element.return_value = mock_next_button
        
        # Réinitialisation et configuration du fetcher
        self.fetcher.driver = mock_driver
        self.fetcher.username = "test_user"
        self.fetcher.password = "test_pass"
        
        # Exécution du login
        self.fetcher.login()
        
        # Vérifications
        mock_driver.get.assert_called_with('https://twitter.com/login')
        mock_element.send_keys.assert_any_call("test_user")
        mock_element.send_keys.assert_any_call("test_pass")

    @patch('selenium.webdriver.Chrome')
    def test_scroll_page(self, mock_chrome):
        """Test du scroll de la page."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock des tweets
        mock_tweet1 = MagicMock(spec=WebElement)
        mock_tweet2 = MagicMock(spec=WebElement)
        mock_driver.find_elements.return_value = [mock_tweet1, mock_tweet2]
        
        # Mock de execute_script
        mock_driver.execute_script.return_value = 1000
        
        self.fetcher.driver = mock_driver
        tweets = self.fetcher.scroll_page(mock_driver, max_tweets=2)
        
        self.assertEqual(len(tweets), 2)
        mock_driver.execute_script.assert_called()

    @patch('selenium.webdriver.Chrome')
    def test_extract_tweet_data(self, mock_chrome):
        """Test de l'extraction des données d'un tweet."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock des éléments du tweet
        mock_text_element = MagicMock(spec=WebElement)
        mock_date_element = MagicMock(spec=WebElement)
        mock_metrics_elements = [MagicMock(spec=WebElement) for _ in range(3)]
        mock_hashtag_elements = [MagicMock(spec=WebElement) for _ in range(2)]
        
        mock_tweet = MagicMock(spec=WebElement)
        
        # Configuration du mock pour find_element
        def mock_find_element(by, value):
            if 'tweetText' in value:
                return mock_text_element
            elif 'time' in value:
                return mock_date_element
            return None
            
        mock_tweet.find_element.side_effect = mock_find_element
        
        # Configuration des valeurs retournées
        mock_text_element.text = "Test tweet"
        mock_date_element.get_attribute.return_value = "2024-03-20T10:00:00Z"
        
        for i, elem in enumerate(mock_metrics_elements):
            elem.get_attribute.return_value = f"metric{i}"
            elem.text = str(i * 10)
            
        for elem in mock_hashtag_elements:
            elem.text = "Test"
            
        mock_tweet.find_elements.side_effect = [mock_metrics_elements, mock_hashtag_elements]
        
        self.fetcher.driver = mock_driver
        result = self.fetcher.extract_tweet_data(mock_tweet)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['text'], "Test tweet")
        self.assertEqual(result['date'], "2024-03-20T10:00:00Z")
        self.assertIn('metrics', result)
        self.assertIn('hashtags', result)

    @patch('selenium.webdriver.Chrome')
    def test_fetch_account_tweets(self, mock_chrome):
        """Test de la récupération des tweets d'un compte."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock des éléments nécessaires
        mock_tweet = MagicMock(spec=WebElement)
        mock_driver.find_elements.return_value = [mock_tweet]
        
        # Mock de WebDriverWait
        mock_wait = MagicMock()
        mock_wait.until.return_value = mock_tweet
        
        with patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
            self.fetcher.driver = mock_driver
            tweets = self.fetcher.fetch_account_tweets("test_account", max_tweets=1)
            
            self.assertIsInstance(tweets, list)
            mock_driver.get.assert_called_once()

if __name__ == '__main__':
    unittest.main() 