import os
import re
import json
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from textblob import TextBlob
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedSentimentAnalyzer:
    def __init__(self):
        """Initialise l'analyseur de sentiment avancé."""
        load_dotenv()
        
        # Téléchargement des ressources NLTK nécessaires
        self._download_nltk_resources()
        
        # Initialisation des analyseurs
        self.sia = SentimentIntensityAnalyzer()
        
        # Dictionnaire de mots crypto-spécifiques
        self.crypto_lexicon = {
            # Positifs
            'moon': 3.0, 'bullish': 2.5, 'pump': 2.0, 'ath': 2.5, 'breakout': 2.0,
            'hodl': 1.5, 'buy': 1.5, 'long': 1.5, 'support': 1.5, 'resistance': 1.0,
            'accumulation': 2.0, 'uptrend': 2.0, 'recovery': 1.5, 'green': 1.5,
            'profit': 2.0, 'gains': 2.0, 'surge': 2.5, 'soar': 2.5, 'rally': 2.0,
            # Négatifs
            'dump': -2.5, 'bearish': -2.5, 'crash': -3.0, 'sell': -1.5, 'short': -1.5,
            'fud': -2.0, 'scam': -3.0, 'rug': -3.0, 'rekt': -2.5, 'dip': -1.5,
            'correction': -1.0, 'downtrend': -2.0, 'loss': -2.0, 'red': -1.5,
            'panic': -2.5, 'fear': -2.0, 'plunge': -2.5, 'collapse': -3.0
        }
        
        # Patterns de détection
        self.price_patterns = {
            'targets': re.compile(r'\$?\d+[kKmM]?\s*(target|pt|price\s*target)', re.IGNORECASE),
            'predictions': re.compile(r'(will|could|might|should)\s*(reach|hit|touch)\s*\$?\d+', re.IGNORECASE),
            'support_resistance': re.compile(r'(support|resistance)\s*(at|around|near)\s*\$?\d+', re.IGNORECASE)
        }
        
        # Émojis et leur sentiment
        self.emoji_sentiments = {
            '🚀': 3.0, '🌙': 3.0, '💎': 2.5, '🙌': 2.0, '📈': 2.0, '💰': 2.0,
            '🔥': 2.0, '✅': 1.5, '👍': 1.5, '💪': 1.5, '🎯': 1.5,
            '📉': -2.0, '💩': -2.5, '🐻': -2.0, '⚠️': -1.5, '🚨': -2.0,
            '❌': -2.0, '👎': -1.5, '😱': -2.0, '😰': -1.5, '🩸': -2.5
        }
        
        # Cache pour les résultats
        self._cache = {}
        
    def _download_nltk_resources(self):
        """Télécharge les ressources NLTK nécessaires."""
        resources = ['vader_lexicon', 'punkt', 'stopwords', 'averaged_perceptron_tagger']
        for resource in resources:
            try:
                nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else f'corpora/{resource}')
            except LookupError:
                nltk.download(resource)
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyse le sentiment d'un texte avec plusieurs méthodes."""
        # Vérification du cache
        cache_key = hash(text)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Prétraitement
        clean_text = self._preprocess_text(text)
        
        # Analyse VADER
        vader_scores = self.sia.polarity_scores(text)
        
        # Analyse TextBlob
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity
        
        # Analyse personnalisée crypto
        crypto_score = self._calculate_crypto_sentiment(text)
        
        # Analyse des émojis
        emoji_score = self._analyze_emojis(text)
        
        # Score composite
        composite_score = self._calculate_composite_score({
            'vader': vader_scores['compound'],
            'textblob': textblob_polarity,
            'crypto': crypto_score,
            'emoji': emoji_score
        })
        
        # Catégorisation
        sentiment_category = self._categorize_sentiment(composite_score)
        
        # Extraction d'insights
        insights = self._extract_insights(text)
        
        result = {
            'text': text[:200] + '...' if len(text) > 200 else text,
            'scores': {
                'vader': vader_scores,
                'textblob': {'polarity': textblob_polarity, 'subjectivity': textblob_subjectivity},
                'crypto': crypto_score,
                'emoji': emoji_score,
                'composite': composite_score
            },
            'category': sentiment_category,
            'confidence': self._calculate_confidence(vader_scores, textblob_polarity),
            'insights': insights,
            'timestamp': datetime.now().isoformat()
        }
        
        # Mise en cache
        self._cache[cache_key] = result
        
        return result
    
    def _preprocess_text(self, text: str) -> str:
        """Prétraite le texte pour l'analyse."""
        # Conversion en minuscules
        text = text.lower()
        
        # Suppression des URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Suppression des mentions
        text = re.sub(r'@\w+', '', text)
        
        # Normalisation des espaces
        text = ' '.join(text.split())
        
        return text
    
    def _calculate_crypto_sentiment(self, text: str) -> float:
        """Calcule le sentiment basé sur le lexique crypto."""
        words = word_tokenize(text.lower())
        score = 0
        count = 0
        
        for word in words:
            if word in self.crypto_lexicon:
                score += self.crypto_lexicon[word]
                count += 1
        
        if count == 0:
            return 0.0
        
        # Normalisation entre -1 et 1
        normalized_score = score / count / 3.0
        return max(-1.0, min(1.0, normalized_score))
    
    def _analyze_emojis(self, text: str) -> float:
        """Analyse le sentiment des émojis."""
        score = 0
        count = 0
        
        for emoji, sentiment in self.emoji_sentiments.items():
            occurrences = text.count(emoji)
            if occurrences > 0:
                score += sentiment * occurrences
                count += occurrences
        
        if count == 0:
            return 0.0
        
        # Normalisation entre -1 et 1
        normalized_score = score / count / 3.0
        return max(-1.0, min(1.0, normalized_score))
    
    def _calculate_composite_score(self, scores: Dict[str, float]) -> float:
        """Calcule un score composite pondéré."""
        weights = {
            'vader': 0.3,
            'textblob': 0.2,
            'crypto': 0.35,
            'emoji': 0.15
        }
        
        weighted_sum = sum(scores[key] * weights[key] for key in scores if key in weights)
        return max(-1.0, min(1.0, weighted_sum))
    
    def _categorize_sentiment(self, score: float) -> str:
        """Catégorise le sentiment basé sur le score."""
        if score >= 0.5:
            return "très_positif"
        elif score >= 0.1:
            return "positif"
        elif score >= -0.1:
            return "neutre"
        elif score >= -0.5:
            return "négatif"
        else:
            return "très_négatif"
    
    def _calculate_confidence(self, vader_scores: Dict, textblob_polarity: float) -> float:
        """Calcule la confiance dans l'analyse."""
        # Accord entre VADER et TextBlob
        vader_sentiment = vader_scores['compound']
        agreement = 1.0 - abs(vader_sentiment - textblob_polarity)
        
        # Force du sentiment (pas trop neutre)
        strength = abs(vader_sentiment) + abs(textblob_polarity)
        
        # Confiance finale
        confidence = (agreement * 0.6 + min(strength, 1.0) * 0.4)
        return round(confidence, 2)
    
    def _extract_insights(self, text: str) -> Dict[str, Any]:
        """Extrait des insights spécifiques du texte."""
        insights = {
            'mentioned_cryptos': self._extract_crypto_mentions(text),
            'price_targets': self._extract_price_targets(text),
            'key_topics': self._extract_key_topics(text),
            'urgency_indicators': self._detect_urgency(text),
            'technical_indicators': self._extract_technical_indicators(text)
        }
        
        return insights
    
    def _extract_crypto_mentions(self, text: str) -> List[str]:
        """Extrait les mentions de cryptomonnaies."""
        crypto_pattern = re.compile(r'\b(bitcoin|btc|ethereum|eth|bnb|sol|solana|ada|cardano|dot|polkadot|'
                                   r'xrp|ripple|doge|dogecoin|avax|avalanche|matic|polygon|link|chainlink|'
                                   r'atom|cosmos|arb|arbitrum|op|optimism|apt|aptos)\b', re.IGNORECASE)
        
        matches = crypto_pattern.findall(text)
        # Normalisation et déduplication
        normalized = []
        seen = set()
        
        crypto_map = {
            'btc': 'bitcoin', 'eth': 'ethereum', 'sol': 'solana',
            'ada': 'cardano', 'dot': 'polkadot', 'xrp': 'ripple',
            'doge': 'dogecoin', 'avax': 'avalanche', 'matic': 'polygon',
            'link': 'chainlink', 'atom': 'cosmos', 'arb': 'arbitrum',
            'op': 'optimism', 'apt': 'aptos'
        }
        
        for match in matches:
            normalized_name = crypto_map.get(match.lower(), match.lower())
            if normalized_name not in seen:
                seen.add(normalized_name)
                normalized.append(normalized_name.upper())
        
        return normalized
    
    def _extract_price_targets(self, text: str) -> List[Dict[str, Any]]:
        """Extrait les objectifs de prix mentionnés."""
        targets = []
        
        # Pattern pour détecter les prix
        price_pattern = re.compile(r'\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*([kKmMbB]?)', re.IGNORECASE)
        
        for pattern_name, pattern in self.price_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                price_matches = price_pattern.findall(match.group())
                for price_match in price_matches:
                    value = float(price_match[0].replace(',', ''))
                    multiplier = price_match[1].lower()
                    
                    if multiplier == 'k':
                        value *= 1000
                    elif multiplier == 'm':
                        value *= 1000000
                    elif multiplier == 'b':
                        value *= 1000000000
                    
                    targets.append({
                        'type': pattern_name,
                        'value': value,
                        'context': match.group()[:100]
                    })
        
        return targets
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extrait les sujets clés du texte."""
        # Suppression des mots vides
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(text.lower())
        words = [w for w in words if w.isalnum() and w not in stop_words and len(w) > 3]
        
        # Comptage des mots
        word_freq = Counter(words)
        
        # Topics crypto spécifiques
        crypto_topics = {
            'defi': ['defi', 'yield', 'farming', 'liquidity', 'swap', 'amm'],
            'nft': ['nft', 'opensea', 'collection', 'mint', 'artwork'],
            'trading': ['trading', 'chart', 'technical', 'analysis', 'indicator'],
            'regulation': ['sec', 'regulation', 'compliance', 'legal', 'government'],
            'technology': ['blockchain', 'smart', 'contract', 'protocol', 'upgrade']
        }
        
        detected_topics = []
        for topic, keywords in crypto_topics.items():
            if any(keyword in words for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics
    
    def _detect_urgency(self, text: str) -> Dict[str, Any]:
        """Détecte les indicateurs d'urgence dans le texte."""
        urgency_words = {
            'high': ['urgent', 'immediately', 'now', 'asap', 'breaking', 'alert'],
            'medium': ['soon', 'coming', 'upcoming', 'prepare', 'ready'],
            'low': ['eventually', 'future', 'long-term', 'patience', 'hold']
        }
        
        text_lower = text.lower()
        urgency_level = 'low'
        detected_words = []
        
        for level, words in urgency_words.items():
            for word in words:
                if word in text_lower:
                    detected_words.append(word)
                    if level == 'high':
                        urgency_level = 'high'
                    elif level == 'medium' and urgency_level != 'high':
                        urgency_level = 'medium'
        
        return {
            'level': urgency_level,
            'indicators': detected_words
        }
    
    def _extract_technical_indicators(self, text: str) -> List[str]:
        """Extrait les indicateurs techniques mentionnés."""
        indicators = [
            'rsi', 'macd', 'ema', 'sma', 'bollinger', 'fibonacci',
            'support', 'resistance', 'volume', 'momentum', 'divergence'
        ]
        
        text_lower = text.lower()
        found_indicators = []
        
        for indicator in indicators:
            if indicator in text_lower:
                found_indicators.append(indicator.upper())
        
        return found_indicators
    
    def analyze_batch(self, texts: List[str]) -> Dict[str, Any]:
        """Analyse un lot de textes et retourne des statistiques agrégées."""
        results = []
        sentiments = []
        all_cryptos = []
        all_topics = []
        
        for text in texts:
            analysis = self.analyze_text_sentiment(text)
            results.append(analysis)
            sentiments.append(analysis['scores']['composite'])
            all_cryptos.extend(analysis['insights']['mentioned_cryptos'])
            all_topics.extend(analysis['insights']['key_topics'])
        
        # Calcul des statistiques
        sentiment_array = np.array(sentiments)
        
        return {
            'total_analyzed': len(texts),
            'average_sentiment': float(np.mean(sentiment_array)),
            'sentiment_std': float(np.std(sentiment_array)),
            'sentiment_distribution': {
                'très_positif': sum(1 for r in results if r['category'] == 'très_positif'),
                'positif': sum(1 for r in results if r['category'] == 'positif'),
                'neutre': sum(1 for r in results if r['category'] == 'neutre'),
                'négatif': sum(1 for r in results if r['category'] == 'négatif'),
                'très_négatif': sum(1 for r in results if r['category'] == 'très_négatif')
            },
            'top_mentioned_cryptos': Counter(all_cryptos).most_common(10),
            'trending_topics': Counter(all_topics).most_common(5),
            'detailed_results': results
        }
    
    def generate_sentiment_report(self, analysis_results: Dict[str, Any]) -> str:
        """Génère un rapport de sentiment formaté."""
        report = f"""
📊 RAPPORT D'ANALYSE DE SENTIMENT CRYPTO
{'='*50}

📈 Résumé Global:
- Textes analysés: {analysis_results['total_analyzed']}
- Sentiment moyen: {analysis_results['average_sentiment']:.3f} ({self._categorize_sentiment(analysis_results['average_sentiment'])})
- Écart-type: {analysis_results['sentiment_std']:.3f}

📊 Distribution des Sentiments:
"""
        
        for category, count in analysis_results['sentiment_distribution'].items():
            percentage = (count / analysis_results['total_analyzed']) * 100
            emoji = {
                'très_positif': '🚀',
                'positif': '📈',
                'neutre': '➖',
                'négatif': '📉',
                'très_négatif': '💥'
            }.get(category, '')
            report += f"  {emoji} {category}: {count} ({percentage:.1f}%)\n"
        
        report += f"\n💰 Top 10 Cryptos Mentionnées:\n"
        for crypto, count in analysis_results['top_mentioned_cryptos']:
            report += f"  • {crypto}: {count} mentions\n"
        
        report += f"\n🏷️ Sujets Tendances:\n"
        for topic, count in analysis_results['trending_topics']:
            report += f"  • {topic}: {count} occurrences\n"
        
        report += f"\n{'='*50}\n"
        report += f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report