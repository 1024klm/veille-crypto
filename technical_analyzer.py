import numpy as np
import pandas as pd
import talib
import requests
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from cache_manager import cache_manager
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    def __init__(self):
        """Initialise l'analyseur technique."""
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        
        # Configuration des indicateurs
        self.indicators_config = {
            'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'bb': {'period': 20, 'std_dev': 2},
            'ema': {'periods': [9, 21, 50, 200]},
            'sma': {'periods': [20, 50, 200]},
            'stoch': {'fastk': 14, 'slowk': 3, 'slowd': 3}
        }
        
        # Niveaux de support/résistance Fibonacci
        self.fib_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        
    @cache_manager.cache_result(prefix='technical_analysis', ttl=900)
    def get_ohlcv_data(self, coin_id: str, vs_currency: str = 'usd', days: int = 30) -> pd.DataFrame:
        """Récupère les données OHLCV depuis CoinGecko."""
        try:
            url = f"{self.coingecko_base_url}/coins/{coin_id}/ohlc"
            params = {
                'vs_currency': vs_currency,
                'days': days
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Conversion en DataFrame
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Ajout du volume (approximé si non disponible)
            df['volume'] = df['close'] * 1000000  # Volume approximé
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données OHLCV: {str(e)}")
            return pd.DataFrame()
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        """Calcule le RSI (Relative Strength Index)."""
        return talib.RSI(df['close'], timeperiod=self.indicators_config['rsi']['period'])
    
    def calculate_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calcule le MACD (Moving Average Convergence Divergence)."""
        macd, signal, hist = talib.MACD(
            df['close'],
            fastperiod=self.indicators_config['macd']['fast'],
            slowperiod=self.indicators_config['macd']['slow'],
            signalperiod=self.indicators_config['macd']['signal']
        )
        return macd, signal, hist
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calcule les Bandes de Bollinger."""
        upper, middle, lower = talib.BBANDS(
            df['close'],
            timeperiod=self.indicators_config['bb']['period'],
            nbdevup=self.indicators_config['bb']['std_dev'],
            nbdevdn=self.indicators_config['bb']['std_dev']
        )
        return upper, middle, lower
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calcule les moyennes mobiles."""
        ma_dict = {}
        
        # EMA
        for period in self.indicators_config['ema']['periods']:
            ma_dict[f'EMA_{period}'] = talib.EMA(df['close'], timeperiod=period)
        
        # SMA
        for period in self.indicators_config['sma']['periods']:
            ma_dict[f'SMA_{period}'] = talib.SMA(df['close'], timeperiod=period)
        
        return ma_dict
    
    def calculate_stochastic(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Calcule l'oscillateur stochastique."""
        slowk, slowd = talib.STOCH(
            df['high'], df['low'], df['close'],
            fastk_period=self.indicators_config['stoch']['fastk'],
            slowk_period=self.indicators_config['stoch']['slowk'],
            slowd_period=self.indicators_config['stoch']['slowd']
        )
        return slowk, slowd
    
    def calculate_fibonacci_levels(self, df: pd.DataFrame) -> Dict[float, float]:
        """Calcule les niveaux de retracement de Fibonacci."""
        high = df['high'].max()
        low = df['low'].min()
        diff = high - low
        
        fib_levels = {}
        for level in self.fib_levels:
            fib_levels[level] = high - (diff * level)
        
        return fib_levels
    
    def detect_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
        """Détecte les niveaux de support et résistance."""
        # Utilisation des points pivots
        pivots_high = df['high'].rolling(window=window, center=True).max()
        pivots_low = df['low'].rolling(window=window, center=True).min()
        
        # Identification des niveaux significatifs
        resistance_levels = []
        support_levels = []
        
        # Résistances : points où le prix a été rejeté plusieurs fois
        for i in range(window, len(df) - window):
            if df['high'].iloc[i] == pivots_high.iloc[i]:
                resistance_levels.append(df['high'].iloc[i])
        
        # Supports : points où le prix a rebondi plusieurs fois
        for i in range(window, len(df) - window):
            if df['low'].iloc[i] == pivots_low.iloc[i]:
                support_levels.append(df['low'].iloc[i])
        
        # Regroupement des niveaux proches
        def cluster_levels(levels, threshold=0.02):
            if not levels:
                return []
            
            sorted_levels = sorted(levels)
            clusters = [[sorted_levels[0]]]
            
            for level in sorted_levels[1:]:
                if (level - clusters[-1][-1]) / clusters[-1][-1] < threshold:
                    clusters[-1].append(level)
                else:
                    clusters.append([level])
            
            return [np.mean(cluster) for cluster in clusters]
        
        return {
            'resistance': cluster_levels(resistance_levels),
            'support': cluster_levels(support_levels)
        }
    
    def identify_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identifie les patterns de chandeliers japonais."""
        patterns = []
        
        # Patterns haussiers
        bullish_patterns = {
            'HAMMER': talib.CDLHAMMER,
            'MORNING_STAR': talib.CDLMORNINGSTAR,
            'BULLISH_ENGULFING': talib.CDLENGULFING,
            'THREE_WHITE_SOLDIERS': talib.CDL3WHITESOLDIERS
        }
        
        # Patterns baissiers
        bearish_patterns = {
            'SHOOTING_STAR': talib.CDLSHOOTINGSTAR,
            'EVENING_STAR': talib.CDLEVENINGSTAR,
            'BEARISH_ENGULFING': talib.CDLENGULFING,
            'THREE_BLACK_CROWS': talib.CDL3BLACKCROWS
        }
        
        for name, func in bullish_patterns.items():
            result = func(df['open'], df['high'], df['low'], df['close'])
            if result.iloc[-1] > 0:
                patterns.append({
                    'pattern': name,
                    'type': 'bullish',
                    'strength': result.iloc[-1],
                    'timestamp': df.index[-1]
                })
        
        for name, func in bearish_patterns.items():
            result = func(df['open'], df['high'], df['low'], df['close'])
            if result.iloc[-1] < 0:
                patterns.append({
                    'pattern': name,
                    'type': 'bearish',
                    'strength': abs(result.iloc[-1]),
                    'timestamp': df.index[-1]
                })
        
        return patterns
    
    def generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Génère des signaux de trading basés sur l'analyse technique."""
        signals = {
            'action': 'NEUTRAL',
            'strength': 0,
            'reasons': []
        }
        
        buy_signals = 0
        sell_signals = 0
        
        # Signal RSI
        rsi_value = analysis['indicators']['rsi']['value']
        if rsi_value < self.indicators_config['rsi']['oversold']:
            buy_signals += 1
            signals['reasons'].append(f"RSI survendu ({rsi_value:.1f})")
        elif rsi_value > self.indicators_config['rsi']['overbought']:
            sell_signals += 1
            signals['reasons'].append(f"RSI suracheté ({rsi_value:.1f})")
        
        # Signal MACD
        if analysis['indicators']['macd']['histogram'] > 0:
            if analysis['indicators']['macd']['trend'] == 'bullish_crossover':
                buy_signals += 2
                signals['reasons'].append("Croisement MACD haussier")
        elif analysis['indicators']['macd']['histogram'] < 0:
            if analysis['indicators']['macd']['trend'] == 'bearish_crossover':
                sell_signals += 2
                signals['reasons'].append("Croisement MACD baissier")
        
        # Signal Bollinger Bands
        bb_position = analysis['indicators']['bollinger_bands']['position']
        if bb_position == 'below_lower':
            buy_signals += 1
            signals['reasons'].append("Prix sous la bande inférieure")
        elif bb_position == 'above_upper':
            sell_signals += 1
            signals['reasons'].append("Prix au-dessus de la bande supérieure")
        
        # Signal MA
        ma_trend = analysis['indicators']['moving_averages']['trend']
        if ma_trend == 'strong_bullish':
            buy_signals += 1
            signals['reasons'].append("Tendance MA fortement haussière")
        elif ma_trend == 'strong_bearish':
            sell_signals += 1
            signals['reasons'].append("Tendance MA fortement baissière")
        
        # Détermination du signal final
        total_signals = buy_signals + sell_signals
        if total_signals > 0:
            if buy_signals > sell_signals:
                signals['action'] = 'BUY'
                signals['strength'] = buy_signals / total_signals
            elif sell_signals > buy_signals:
                signals['action'] = 'SELL'
                signals['strength'] = sell_signals / total_signals
        
        return signals
    
    def create_analysis_chart(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> str:
        """Crée un graphique d'analyse technique."""
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        
        # Graphique principal avec prix et moyennes mobiles
        ax1.plot(df.index, df['close'], 'b-', label='Prix')
        
        # Moyennes mobiles
        for ma_name, ma_values in analysis['indicators']['moving_averages']['values'].items():
            if 'EMA' in ma_name and '50' not in ma_name and '200' not in ma_name:
                ax1.plot(df.index, ma_values, label=ma_name)
        
        # Bandes de Bollinger
        bb = analysis['indicators']['bollinger_bands']['bands']
        ax1.fill_between(df.index, bb['lower'], bb['upper'], alpha=0.2, color='gray')
        ax1.plot(df.index, bb['middle'], 'g--', alpha=0.5, label='BB Middle')
        
        ax1.set_ylabel('Prix (USD)')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # RSI
        rsi_values = analysis['indicators']['rsi']['series']
        ax2.plot(df.index, rsi_values, 'purple', label='RSI')
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5)
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5)
        ax2.fill_between(df.index, 30, 70, alpha=0.1, color='gray')
        ax2.set_ylabel('RSI')
        ax2.set_ylim(0, 100)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        # MACD
        macd = analysis['indicators']['macd']
        ax3.plot(df.index, macd['macd'], 'b-', label='MACD')
        ax3.plot(df.index, macd['signal'], 'r-', label='Signal')
        ax3.bar(df.index, macd['histogram'], alpha=0.3, label='Histogram')
        ax3.set_ylabel('MACD')
        ax3.set_xlabel('Date')
        ax3.legend(loc='upper left')
        ax3.grid(True, alpha=0.3)
        
        # Format des dates
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Conversion en base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def analyze_coin(self, coin_id: str, days: int = 30) -> Dict[str, Any]:
        """Effectue une analyse technique complète d'une crypto."""
        # Récupération des données
        df = self.get_ohlcv_data(coin_id, days=days)
        
        if df.empty:
            return {'error': 'Impossible de récupérer les données'}
        
        # Calcul des indicateurs
        rsi = self.calculate_rsi(df)
        macd, signal, hist = self.calculate_macd(df)
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(df)
        moving_averages = self.calculate_moving_averages(df)
        stoch_k, stoch_d = self.calculate_stochastic(df)
        fib_levels = self.calculate_fibonacci_levels(df)
        support_resistance = self.detect_support_resistance(df)
        patterns = self.identify_patterns(df)
        
        # Analyse des tendances
        current_price = df['close'].iloc[-1]
        
        # Position par rapport aux Bollinger Bands
        bb_position = 'neutral'
        if current_price < bb_lower.iloc[-1]:
            bb_position = 'below_lower'
        elif current_price > bb_upper.iloc[-1]:
            bb_position = 'above_upper'
        
        # Tendance des moyennes mobiles
        ma_trend = 'neutral'
        ema_9 = moving_averages['EMA_9'].iloc[-1]
        ema_21 = moving_averages['EMA_21'].iloc[-1]
        sma_50 = moving_averages['SMA_50'].iloc[-1]
        
        if ema_9 > ema_21 > sma_50:
            ma_trend = 'strong_bullish'
        elif ema_9 < ema_21 < sma_50:
            ma_trend = 'strong_bearish'
        elif ema_9 > ema_21:
            ma_trend = 'bullish'
        elif ema_9 < ema_21:
            ma_trend = 'bearish'
        
        # Détection de divergences
        def detect_divergence(price_data, indicator_data, window=5):
            if len(price_data) < window * 2:
                return 'none'
            
            # Prix : higher highs ou lower lows
            recent_highs = price_data.rolling(window=window).max()
            recent_lows = price_data.rolling(window=window).min()
            
            price_trend = 'neutral'
            if recent_highs.iloc[-1] > recent_highs.iloc[-window]:
                price_trend = 'up'
            elif recent_lows.iloc[-1] < recent_lows.iloc[-window]:
                price_trend = 'down'
            
            # Indicateur : direction opposée?
            indicator_trend = 'neutral'
            if indicator_data.iloc[-1] > indicator_data.iloc[-window]:
                indicator_trend = 'up'
            elif indicator_data.iloc[-1] < indicator_data.iloc[-window]:
                indicator_trend = 'down'
            
            if price_trend == 'up' and indicator_trend == 'down':
                return 'bearish_divergence'
            elif price_trend == 'down' and indicator_trend == 'up':
                return 'bullish_divergence'
            
            return 'none'
        
        rsi_divergence = detect_divergence(df['close'], rsi)
        
        # Préparation du résultat
        analysis = {
            'coin_id': coin_id,
            'timestamp': datetime.now().isoformat(),
            'current_price': current_price,
            'price_change_24h': ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100) if len(df) > 24 else 0,
            'indicators': {
                'rsi': {
                    'value': rsi.iloc[-1],
                    'status': 'oversold' if rsi.iloc[-1] < 30 else 'overbought' if rsi.iloc[-1] > 70 else 'neutral',
                    'divergence': rsi_divergence,
                    'series': rsi
                },
                'macd': {
                    'macd': macd,
                    'signal': signal,
                    'histogram': hist.iloc[-1],
                    'trend': 'bullish_crossover' if hist.iloc[-1] > 0 and hist.iloc[-2] <= 0 else 
                            'bearish_crossover' if hist.iloc[-1] < 0 and hist.iloc[-2] >= 0 else 'neutral'
                },
                'bollinger_bands': {
                    'upper': bb_upper.iloc[-1],
                    'middle': bb_middle.iloc[-1],
                    'lower': bb_lower.iloc[-1],
                    'position': bb_position,
                    'bands': {'upper': bb_upper, 'middle': bb_middle, 'lower': bb_lower}
                },
                'moving_averages': {
                    'values': moving_averages,
                    'trend': ma_trend,
                    'ema_9': ema_9,
                    'ema_21': ema_21,
                    'sma_50': sma_50
                },
                'stochastic': {
                    'k': stoch_k.iloc[-1],
                    'd': stoch_d.iloc[-1],
                    'status': 'oversold' if stoch_k.iloc[-1] < 20 else 'overbought' if stoch_k.iloc[-1] > 80 else 'neutral'
                }
            },
            'levels': {
                'fibonacci': fib_levels,
                'support': support_resistance['support'][:3],  # Top 3 supports
                'resistance': support_resistance['resistance'][:3]  # Top 3 resistances
            },
            'patterns': patterns[-5:] if patterns else [],  # 5 derniers patterns
            'data': df
        }
        
        # Génération des signaux
        analysis['signals'] = self.generate_signals(analysis)
        
        # Création du graphique
        try:
            analysis['chart'] = self.create_analysis_chart(df, analysis)
        except Exception as e:
            logger.error(f"Erreur lors de la création du graphique: {str(e)}")
            analysis['chart'] = None
        
        return analysis
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """Génère un rapport d'analyse technique formaté."""
        report = f"""
📊 RAPPORT D'ANALYSE TECHNIQUE - {analysis['coin_id'].upper()}
{'='*60}

💰 Prix actuel: ${analysis['current_price']:.4f}
📈 Variation 24h: {analysis['price_change_24h']:.2f}%

🔍 INDICATEURS TECHNIQUES:

RSI (14): {analysis['indicators']['rsi']['value']:.2f} - {analysis['indicators']['rsi']['status'].upper()}
{'⚠️ Divergence ' + analysis['indicators']['rsi']['divergence'] if analysis['indicators']['rsi']['divergence'] != 'none' else ''}

MACD: {analysis['indicators']['macd']['trend'].replace('_', ' ').title()}
- Histogramme: {analysis['indicators']['macd']['histogram']:.4f}

Bandes de Bollinger: Prix {analysis['indicators']['bollinger_bands']['position'].replace('_', ' ')}
- Supérieure: ${analysis['indicators']['bollinger_bands']['upper']:.4f}
- Moyenne: ${analysis['indicators']['bollinger_bands']['middle']:.4f}
- Inférieure: ${analysis['indicators']['bollinger_bands']['lower']:.4f}

Moyennes Mobiles: Tendance {analysis['indicators']['moving_averages']['trend'].replace('_', ' ').upper()}
- EMA 9: ${analysis['indicators']['moving_averages']['ema_9']:.4f}
- EMA 21: ${analysis['indicators']['moving_averages']['ema_21']:.4f}
- SMA 50: ${analysis['indicators']['moving_averages']['sma_50']:.4f}

Stochastique: {analysis['indicators']['stochastic']['status'].upper()}
- %K: {analysis['indicators']['stochastic']['k']:.2f}
- %D: {analysis['indicators']['stochastic']['d']:.2f}

📏 NIVEAUX CLÉS:

Résistances:
"""
        for i, resistance in enumerate(analysis['levels']['resistance'], 1):
            report += f"  R{i}: ${resistance:.4f}\n"
        
        report += "\nSupports:\n"
        for i, support in enumerate(analysis['levels']['support'], 1):
            report += f"  S{i}: ${support:.4f}\n"
        
        if analysis['patterns']:
            report += "\n🕯️ PATTERNS DÉTECTÉS:\n"
            for pattern in analysis['patterns']:
                emoji = '🟢' if pattern['type'] == 'bullish' else '🔴'
                report += f"  {emoji} {pattern['pattern'].replace('_', ' ').title()} (Force: {pattern['strength']})\n"
        
        report += f"\n💡 SIGNAL: {analysis['signals']['action']} (Force: {analysis['signals']['strength']:.2f})\n"
        if analysis['signals']['reasons']:
            report += "Raisons:\n"
            for reason in analysis['signals']['reasons']:
                report += f"  • {reason}\n"
        
        report += f"\n{'='*60}\n"
        report += f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report