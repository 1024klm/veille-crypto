import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import deque
import json
import os
from cache_manager import cache_manager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self):
        """Initialise le détecteur d'anomalies."""
        self.scaler = StandardScaler()
        
        # Modèles de détection
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        
        # Historique pour la détection en temps réel
        self.price_history = {}
        self.volume_history = {}
        self.sentiment_history = deque(maxlen=100)
        
        # Seuils de détection
        self.thresholds = {
            'price_spike': 0.15,  # 15% en 1 heure
            'volume_spike': 3.0,  # 3x le volume moyen
            'sentiment_shift': 0.5,  # Changement de 0.5 dans le score
            'pattern_confidence': 0.8,  # Confiance minimale pour les patterns
            'whale_threshold': 1000000  # 1M USD
        }
        
        # Patterns d'anomalies connus
        self.anomaly_patterns = {
            'pump_and_dump': {
                'description': 'Hausse rapide suivie d\'une chute brutale',
                'indicators': ['price_spike', 'volume_spike', 'sentiment_spike']
            },
            'flash_crash': {
                'description': 'Chute brutale et rapide du prix',
                'indicators': ['price_drop', 'volume_spike', 'negative_sentiment']
            },
            'whale_manipulation': {
                'description': 'Mouvements importants par des baleines',
                'indicators': ['large_transaction', 'price_movement', 'order_book_imbalance']
            },
            'fomo_rally': {
                'description': 'Hausse irrationnelle due au FOMO',
                'indicators': ['price_spike', 'sentiment_spike', 'social_media_buzz']
            },
            'coordinated_attack': {
                'description': 'Attaque coordonnée sur une crypto',
                'indicators': ['simultaneous_sells', 'negative_sentiment', 'fud_spread']
            }
        }
        
        # Chargement de l'historique si disponible
        self._load_history()
    
    def _load_history(self):
        """Charge l'historique des données."""
        try:
            history_file = 'data/anomaly_history.json'
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
                    # Conversion des listes en deques
                    prices = history.get('prices', {})
                    volumes = history.get('volumes', {})
                    for coin_id, data in prices.items():
                        self.price_history[coin_id] = deque(data, maxlen=1440)
                    for coin_id, data in volumes.items():
                        self.volume_history[coin_id] = deque(data, maxlen=1440)
                    logger.info("Historique des anomalies chargé")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'historique: {str(e)}")
    
    def _save_history(self):
        """Sauvegarde l'historique des données."""
        try:
            history_file = 'data/anomaly_history.json'
            os.makedirs('data', exist_ok=True)

            # Conversion des deques en listes pour la sérialisation JSON
            history = {
                'prices': {k: list(v) for k, v in self.price_history.items()},
                'volumes': {k: list(v) for k, v in self.volume_history.items()},
                'last_update': datetime.now().isoformat()
            }

            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'historique: {str(e)}")
    
    def update_price_history(self, coin_id: str, price: float, volume: float = 0):
        """Met à jour l'historique des prix."""
        timestamp = datetime.now().isoformat()
        
        if coin_id not in self.price_history:
            self.price_history[coin_id] = deque(maxlen=1440)  # 24h de données par minute
            self.volume_history[coin_id] = deque(maxlen=1440)
        
        self.price_history[coin_id].append({
            'timestamp': timestamp,
            'price': price
        })
        
        self.volume_history[coin_id].append({
            'timestamp': timestamp,
            'volume': volume
        })
    
    def detect_price_anomaly(self, coin_id: str, current_price: float) -> Optional[Dict[str, Any]]:
        """Détecte les anomalies de prix."""
        if coin_id not in self.price_history or len(self.price_history[coin_id]) < 60:
            return None
        
        history = list(self.price_history[coin_id])
        
        # Prix il y a 1 heure
        price_1h_ago = history[-60]['price'] if len(history) >= 60 else history[0]['price']
        
        # Calcul du changement
        price_change = (current_price - price_1h_ago) / price_1h_ago
        
        if abs(price_change) >= self.thresholds['price_spike']:
            # Analyse plus approfondie avec ML
            prices = [h['price'] for h in history[-120:]]  # 2 dernières heures
            
            # Détection avec Isolation Forest
            X = np.array(prices).reshape(-1, 1)
            X_scaled = self.scaler.fit_transform(X)
            
            # Prédiction (-1 pour anomalie, 1 pour normal)
            prediction = self.isolation_forest.fit_predict(X_scaled)
            
            if prediction[-1] == -1:  # Anomalie détectée
                return {
                    'type': 'price_anomaly',
                    'coin': coin_id,
                    'severity': 'high' if abs(price_change) > 0.3 else 'medium',
                    'change_1h': price_change,
                    'current_price': current_price,
                    'previous_price': price_1h_ago,
                    'pattern': self._identify_pattern(coin_id, 'price'),
                    'timestamp': datetime.now().isoformat()
                }
        
        return None
    
    def detect_volume_anomaly(self, coin_id: str, current_volume: float) -> Optional[Dict[str, Any]]:
        """Détecte les anomalies de volume."""
        if coin_id not in self.volume_history or len(self.volume_history[coin_id]) < 60:
            return None
        
        history = list(self.volume_history[coin_id])
        volumes = [h['volume'] for h in history[-60:]]  # Dernière heure
        
        avg_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        
        if avg_volume > 0:
            volume_ratio = current_volume / avg_volume
            
            if volume_ratio >= self.thresholds['volume_spike']:
                # Z-score pour mesurer l'anomalie
                z_score = (current_volume - avg_volume) / (std_volume + 1e-8)
                
                if abs(z_score) > 3:  # 3 écarts-types
                    return {
                        'type': 'volume_anomaly',
                        'coin': coin_id,
                        'severity': 'high' if volume_ratio > 5 else 'medium',
                        'volume_ratio': volume_ratio,
                        'z_score': z_score,
                        'current_volume': current_volume,
                        'avg_volume': avg_volume,
                        'timestamp': datetime.now().isoformat()
                    }
        
        return None
    
    def detect_sentiment_anomaly(self, sentiment_score: float) -> Optional[Dict[str, Any]]:
        """Détecte les anomalies de sentiment."""
        self.sentiment_history.append({
            'score': sentiment_score,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.sentiment_history) < 10:
            return None
        
        # Analyse des changements de sentiment
        recent_sentiments = [s['score'] for s in list(self.sentiment_history)[-10:]]
        avg_sentiment = np.mean(recent_sentiments[:-1])
        
        sentiment_change = sentiment_score - avg_sentiment
        
        if abs(sentiment_change) >= self.thresholds['sentiment_shift']:
            return {
                'type': 'sentiment_anomaly',
                'severity': 'high' if abs(sentiment_change) > 0.7 else 'medium',
                'current_sentiment': sentiment_score,
                'average_sentiment': avg_sentiment,
                'change': sentiment_change,
                'direction': 'bullish' if sentiment_change > 0 else 'bearish',
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def _identify_pattern(self, coin_id: str, anomaly_type: str) -> Optional[str]:
        """Identifie le pattern d'anomalie."""
        if coin_id not in self.price_history:
            return None
        
        # Analyse des patterns sur les dernières heures
        price_history = list(self.price_history[coin_id])[-240:]  # 4 heures
        
        if len(price_history) < 60:
            return None
        
        prices = [h['price'] for h in price_history]
        
        # Détection pump and dump
        max_price = max(prices)
        max_idx = prices.index(max_price)
        
        if max_idx > len(prices) // 2:  # Le pic est dans la seconde moitié
            price_before = prices[max_idx - 30] if max_idx >= 30 else prices[0]
            price_after = prices[-1]
            
            pump = (max_price - price_before) / price_before
            dump = (max_price - price_after) / max_price
            
            if pump > 0.3 and dump > 0.2:
                return 'pump_and_dump'
        
        # Détection flash crash
        min_price = min(prices)
        min_idx = prices.index(min_price)
        
        if min_idx > len(prices) - 30:  # Crash récent
            price_before = prices[min_idx - 30] if min_idx >= 30 else prices[0]
            crash = (price_before - min_price) / price_before
            
            if crash > 0.2:
                return 'flash_crash'
        
        # Détection FOMO rally
        recent_prices = prices[-30:]
        if len(recent_prices) == 30:
            consecutive_increases = 0
            for i in range(1, len(recent_prices)):
                if recent_prices[i] > recent_prices[i-1]:
                    consecutive_increases += 1
            
            if consecutive_increases > 20:
                return 'fomo_rally'
        
        return None
    
    def detect_whale_movements(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Détecte les mouvements de baleines suspects."""
        anomalies = []
        
        for tx in transactions:
            if tx.get('amount_usd', 0) >= self.thresholds['whale_threshold']:
                # Analyse du timing et du contexte
                suspicious_score = 0
                
                # Transaction pendant les heures creuses
                hour = datetime.fromisoformat(tx.get('timestamp', datetime.now().isoformat())).hour
                if hour >= 2 and hour <= 6:
                    suspicious_score += 0.3
                
                # Multiple transactions rapprochées
                similar_txs = [
                    t for t in transactions 
                    if t.get('from_address') == tx.get('from_address') 
                    and abs((datetime.fromisoformat(t.get('timestamp', '')) - 
                            datetime.fromisoformat(tx.get('timestamp', ''))).total_seconds()) < 3600
                ]
                
                if len(similar_txs) > 3:
                    suspicious_score += 0.4
                
                # Transaction vers exchange inconnu
                if tx.get('to_exchange', '').lower() in ['unknown', 'mixer', 'tornado']:
                    suspicious_score += 0.3
                
                if suspicious_score >= 0.5:
                    anomalies.append({
                        'type': 'whale_anomaly',
                        'severity': 'high' if suspicious_score > 0.7 else 'medium',
                        'transaction': tx,
                        'suspicious_score': suspicious_score,
                        'reasons': self._get_suspicion_reasons(tx, suspicious_score),
                        'timestamp': datetime.now().isoformat()
                    })
        
        return anomalies
    
    def _get_suspicion_reasons(self, tx: Dict[str, Any], score: float) -> List[str]:
        """Génère les raisons de suspicion."""
        reasons = []
        
        hour = datetime.fromisoformat(tx.get('timestamp', datetime.now().isoformat())).hour
        if hour >= 2 and hour <= 6:
            reasons.append("Transaction pendant les heures creuses")
        
        if tx.get('to_exchange', '').lower() in ['unknown', 'mixer', 'tornado']:
            reasons.append("Destination suspecte")
        
        if score > 0.7:
            reasons.append("Pattern de manipulation détecté")
        
        return reasons
    
    def analyze_market_data(self, market_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Analyse complète des données de marché pour détecter les anomalies."""
        all_anomalies = {
            'price_anomalies': [],
            'volume_anomalies': [],
            'sentiment_anomalies': [],
            'whale_anomalies': [],
            'pattern_anomalies': []
        }
        
        # Analyse des prix et volumes
        if 'prices' in market_data and 'prices' in market_data['prices']:
            for coin, price in market_data['prices']['prices'].items():
                # Mise à jour de l'historique
                volume = market_data['prices'].get('volumes', {}).get(coin, 0)
                self.update_price_history(coin, price, volume)
                
                # Détection d'anomalies
                price_anomaly = self.detect_price_anomaly(coin, price)
                if price_anomaly:
                    all_anomalies['price_anomalies'].append(price_anomaly)
                
                if volume > 0:
                    volume_anomaly = self.detect_volume_anomaly(coin, volume)
                    if volume_anomaly:
                        all_anomalies['volume_anomalies'].append(volume_anomaly)
        
        # Analyse des alertes de baleines
        if 'whale_alerts' in market_data:
            whale_anomalies = self.detect_whale_movements(market_data['whale_alerts'])
            all_anomalies['whale_anomalies'].extend(whale_anomalies)
        
        # Sauvegarde de l'historique
        self._save_history()
        
        return all_anomalies
    
    def generate_anomaly_report(self, anomalies: Dict[str, List[Dict[str, Any]]]) -> str:
        """Génère un rapport d'anomalies formaté."""
        total_anomalies = sum(len(v) for v in anomalies.values())
        
        if total_anomalies == 0:
            return "✅ Aucune anomalie détectée"
        
        report = f"""
🚨 RAPPORT DE DÉTECTION D'ANOMALIES
{'='*50}

Total d'anomalies détectées: {total_anomalies}

"""
        
        # Anomalies de prix
        if anomalies['price_anomalies']:
            report += "💰 ANOMALIES DE PRIX:\n"
            for anomaly in anomalies['price_anomalies']:
                severity_emoji = "🔴" if anomaly['severity'] == 'high' else "🟡"
                report += f"{severity_emoji} {anomaly['coin'].upper()}: "
                report += f"{anomaly['change_1h']:+.1%} en 1h "
                if anomaly.get('pattern'):
                    report += f"(Pattern: {anomaly['pattern']})"
                report += "\n"
            report += "\n"
        
        # Anomalies de volume
        if anomalies['volume_anomalies']:
            report += "📊 ANOMALIES DE VOLUME:\n"
            for anomaly in anomalies['volume_anomalies']:
                severity_emoji = "🔴" if anomaly['severity'] == 'high' else "🟡"
                report += f"{severity_emoji} {anomaly['coin'].upper()}: "
                report += f"Volume x{anomaly['volume_ratio']:.1f} (Z-score: {anomaly['z_score']:.1f})\n"
            report += "\n"
        
        # Anomalies de baleines
        if anomalies['whale_anomalies']:
            report += "🐋 MOUVEMENTS SUSPECTS DE BALEINES:\n"
            for anomaly in anomalies['whale_anomalies']:
                tx = anomaly['transaction']
                report += f"• ${tx.get('amount_usd', 0):,.0f} "
                report += f"{tx.get('symbol', 'UNKNOWN')} "
                report += f"(Score: {anomaly['suspicious_score']:.2f})\n"
                for reason in anomaly['reasons']:
                    report += f"  - {reason}\n"
            report += "\n"
        
        # Recommandations
        report += "💡 RECOMMANDATIONS:\n"
        
        high_severity_count = sum(
            1 for category in anomalies.values() 
            for anomaly in category 
            if anomaly.get('severity') == 'high'
        )
        
        if high_severity_count > 0:
            report += "⚠️ Anomalies de haute sévérité détectées - Prudence recommandée\n"
        
        if any('pump_and_dump' in str(a) for a in anomalies.get('pattern_anomalies', [])):
            report += "⚠️ Pattern pump & dump détecté - Éviter d'acheter au sommet\n"
        
        if any('flash_crash' in str(a) for a in anomalies.get('pattern_anomalies', [])):
            report += "💡 Flash crash détecté - Opportunité d'achat potentielle\n"
        
        report += f"\n{'='*50}\n"
        report += f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    def get_risk_score(self, coin_id: str) -> Dict[str, Any]:
        """Calcule un score de risque pour une crypto."""
        risk_factors = {
            'price_volatility': 0,
            'volume_irregularity': 0,
            'whale_activity': 0,
            'pattern_risk': 0
        }
        
        # Analyse de la volatilité des prix
        if coin_id in self.price_history and len(self.price_history[coin_id]) > 60:
            prices = [h['price'] for h in list(self.price_history[coin_id])[-60:]]
            volatility = np.std(prices) / np.mean(prices)
            risk_factors['price_volatility'] = min(volatility * 10, 1.0)
        
        # Analyse des volumes
        if coin_id in self.volume_history and len(self.volume_history[coin_id]) > 60:
            volumes = [h['volume'] for h in list(self.volume_history[coin_id])[-60:]]
            cv = np.std(volumes) / (np.mean(volumes) + 1e-8)  # Coefficient de variation
            risk_factors['volume_irregularity'] = min(cv / 2, 1.0)
        
        # Pattern de risque
        pattern = self._identify_pattern(coin_id, 'risk')
        if pattern in ['pump_and_dump', 'flash_crash']:
            risk_factors['pattern_risk'] = 0.8
        elif pattern == 'fomo_rally':
            risk_factors['pattern_risk'] = 0.6
        
        # Score global
        total_risk = np.mean(list(risk_factors.values()))
        
        return {
            'coin_id': coin_id,
            'risk_score': round(total_risk, 2),
            'risk_level': 'high' if total_risk > 0.7 else 'medium' if total_risk > 0.4 else 'low',
            'factors': risk_factors,
            'recommendation': self._get_risk_recommendation(total_risk),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_risk_recommendation(self, risk_score: float) -> str:
        """Génère une recommandation basée sur le score de risque."""
        if risk_score > 0.7:
            return "🔴 Risque élevé - Éviter les positions importantes"
        elif risk_score > 0.4:
            return "🟡 Risque modéré - Prudence recommandée"
        else:
            return "🟢 Risque faible - Conditions normales de marché"