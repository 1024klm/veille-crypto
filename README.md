# Veille Crypto Bot 🚀

Bot de veille automatisé ultra-complet pour surveiller l'écosystème crypto 24/7 avec IA, analyse technique, détection d'anomalies et notifications multi-canal.

## 🌟 Fonctionnalités Principales

### 📊 Sources de Données (40+ sources)

1. **Twitter Scraping**
   - 13 comptes crypto majeurs surveillés
   - Analyse d'engagement et extraction de hashtags
   - Résumés intelligents par compte

2. **Flux RSS Étendus**
   - **Médias** : CoinDesk, CoinTelegraph, Decrypt, The Block, Bitcoin Magazine, CryptoSlate
   - **Régulation** : SEC, CFTC, ESMA, IMF
   - **Exchanges** : Binance, Coinbase, Bitget
   - **Newsletters** : The Defiant, Bankless
   - **Analytics** : Glassnode, Santiment, IntoTheBlock, Chainalysis
   - **Sources FR** : JournalDuCoin, Cryptoast, CoinAcademy

3. **APIs de Marché**
   - Prix en temps réel (15+ cryptos majeures)
   - Top 10 cryptos tendances
   - Alertes de mouvements de baleines
   - Données globales du marché (cap, volume)
   - Métriques de sentiment

4. **Données Externes**
   - Google Trends
   - Forums communautaires (BitcoinTalk, HackerNoon)

### 🧠 Intelligence Artificielle

1. **Analyse de Sentiment Avancée**
   - Multi-modèles (VADER, TextBlob, Lexique crypto)
   - Détection d'émojis et leur sentiment
   - Extraction automatique des cryptos mentionnées
   - Identification des objectifs de prix
   - Score de confiance et catégorisation

2. **Détection d'Anomalies ML**
   - Isolation Forest pour anomalies de prix
   - Détection de patterns (pump & dump, flash crash)
   - Analyse des mouvements de baleines suspects
   - Score de risque par crypto
   - Alertes en temps réel

3. **Analyse Technique Complète**
   - RSI, MACD, Bollinger Bands
   - Moyennes mobiles (EMA/SMA multi-périodes)
   - Niveaux de Fibonacci
   - Support/Résistance automatiques
   - Patterns de chandeliers japonais
   - Signaux de trading avec force et raisons
   - Graphiques d'analyse générés

### 🚨 Système de Notifications

1. **Multi-canal**
   - Email (SMTP configurable)
   - Discord (webhooks)
   - Slack (webhooks)
   - Telegram Bot interactif

2. **Types d'Alertes**
   - Changements de prix significatifs
   - Mouvements de baleines
   - Nouvelles cryptos tendances
   - Anomalies détectées
   - Signaux techniques

### 📱 Bot Telegram Complet

- **Commandes** : `/prices`, `/trending`, `/news`, `/sentiment`, `/technical`
- **Interface interactive** avec boutons
- **Alertes automatiques** toutes les 5 minutes
- **Analyse technique** sur demande
- **Gestion de watchlist** personnelle

### 📈 Dashboard Web Interactif

- **Visualisation en temps réel** des prix
- **Graphiques interactifs** (Plotly/Dash)
- **Flux d'alertes** en direct
- **Statistiques globales** du marché
- **Actualités filtrées** par catégorie
- **Mise à jour automatique** toutes les 30 secondes

### 🔧 Optimisations Techniques

1. **Cache Intelligent**
   - Support Redis (optionnel)
   - Cache en mémoire de secours
   - TTL configurables par type de données
   - Statistiques de performance

2. **Gestion d'Erreurs Robuste**
   - Retry automatique
   - Fallback sur sources alternatives
   - Logging détaillé
   - Mode dégradé

## 🚀 Installation

### Prérequis

- Python 3.8+
- Chrome/Chromium (pour Twitter scraping - optionnel)
- Redis (optionnel - pour le cache)
- TA-Lib (pour l'analyse technique)

### Installation Rapide

```bash
# Cloner le repo
git clone https://github.com/1024klm/veille-crypto.git
cd veille-crypto

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer TA-Lib (prérequis pour l'analyse technique)
# Linux : sudo apt-get install ta-lib
# Mac : brew install ta-lib
# Windows : télécharger depuis https://www.ta-lib.org/

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos clés API (toutes optionnelles)

# Télécharger les ressources NLTK (première fois)
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"
```

## 💻 Utilisation

### Mode Gratuit Complet (Recommandé)

```bash
python main.py --free-only
```

### Lancement Standard

```bash
python main.py
```

### Options Disponibles

```bash
# Désactiver des modules spécifiques
python main.py --skip-twitter      # Sans Twitter scraping
python main.py --skip-market       # Sans données de marché
python main.py --skip-external     # Sans sources externes

# Combinaisons
python main.py --skip-twitter --skip-external
```

### Dashboard Web

```bash
python dashboard.py
# Ouvrir http://localhost:8050
```

### Bot Telegram

```bash
# Configurer TELEGRAM_BOT_TOKEN dans .env
python telegram_bot.py
```

### Analyse Technique Standalone

```python
from technical_analyzer import TechnicalAnalyzer

analyzer = TechnicalAnalyzer()
analysis = analyzer.analyze_coin('bitcoin', days=30)
print(analyzer.generate_report(analysis))
```

## 📁 Structure du Projet

```
veille_crypto/
├── data/                       # Données sauvegardées
│   ├── all_data.json          # Toutes les données combinées
│   ├── market_data.json       # Données de marché
│   ├── sentiment_analysis.json # Analyses de sentiment
│   ├── anomalies.json         # Anomalies détectées
│   └── alerts_history.json    # Historique des alertes
├── main.py                    # Script principal
├── dashboard.py               # Dashboard web interactif
├── telegram_bot.py            # Bot Telegram
├── market_data_fetcher.py     # APIs de marché
├── external_sources_fetcher.py # RSS et sources externes
├── twitter_fetcher.py         # Scraping Twitter
├── sentiment_analyzer.py      # Analyse de sentiment IA
├── technical_analyzer.py      # Analyse technique
├── anomaly_detector.py        # Détection d'anomalies ML
├── cache_manager.py           # Gestion du cache
├── notifier.py               # Système de notifications
├── config.py                 # Configuration
├── requirements.txt          # Dépendances Python
├── .env.example             # Exemple de configuration
└── README.md                # Cette documentation
```

## ⚙️ Configuration Avancée

### Variables d'Environnement

```bash
# Twitter (optionnel - pour scraping)
TWITTER_USERNAME=your_username
TWITTER_PASSWORD=your_password
CHROMEDRIVER_PATH=/path/to/chromedriver

# Notifications Email (optionnel)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient1@example.com,recipient2@example.com

# Seuils d'Alerte
PRICE_CHANGE_THRESHOLD=5      # % pour alertes de prix
WHALE_ALERT_THRESHOLD=1000000 # USD pour alertes baleines

# Webhooks (optionnel)
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
SLACK_WEBHOOK=https://hooks.slack.com/services/...

# Telegram Bot (optionnel)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALERT_CHANNELS=channel_id1,channel_id2

# Redis Cache (optionnel)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Google Trends
GOOGLE_TRENDS_GEO=FR
GOOGLE_TRENDS_TIMEFRAME=now 7-d
```

### Personnalisation

1. **Ajouter des Sources RSS**
   ```python
   # Dans external_sources_fetcher.py
   self.rss_feeds['category']['new_source'] = 'https://example.com/rss'
   ```

2. **Modifier les Cryptos Suivies**
   ```python
   # Dans market_data_fetcher.py
   crypto_ids = ['bitcoin', 'ethereum', 'your-crypto']
   ```

3. **Ajuster les Indicateurs Techniques**
   ```python
   # Dans technical_analyzer.py
   self.indicators_config['rsi']['period'] = 21  # Au lieu de 14
   ```

## 🐛 Dépannage

| Problème | Solution |
|----------|----------|
| ChromeDriver error | Installer ChromeDriver et l'ajouter au PATH |
| SSL Certificate error | `pip install certifi` |
| TA-Lib installation | Voir instructions spécifiques OS ci-dessus |
| Redis connection | Installer Redis ou utiliser cache mémoire |
| API rate limit | Utiliser le cache ou espacer les requêtes |

## 📊 Exemples de Données

### Analyse de Sentiment
```json
{
  "average_sentiment": 0.342,
  "sentiment_distribution": {
    "très_positif": 15,
    "positif": 28,
    "neutre": 12,
    "négatif": 8,
    "très_négatif": 2
  },
  "top_mentioned_cryptos": [
    ["BITCOIN", 45],
    ["ETHEREUM", 32],
    ["SOLANA", 18]
  ]
}
```

### Détection d'Anomalie
```json
{
  "type": "price_anomaly",
  "coin": "bitcoin",
  "severity": "high",
  "change_1h": 0.23,
  "pattern": "pump_and_dump",
  "recommendation": "Éviter d'acheter au sommet"
}
```

## 🔄 Automatisation

### Cron Linux/Mac
```bash
# Toutes les heures
0 * * * * cd /path/to/veille_crypto && venv/bin/python main.py --free-only

# Toutes les 15 minutes (intensif)
*/15 * * * * cd /path/to/veille_crypto && venv/bin/python main.py
```

### Task Scheduler Windows
```powershell
# Créer une tâche planifiée
schtasks /create /tn "CryptoVeille" /tr "C:\path\to\python.exe C:\path\to\main.py --free-only" /sc hourly
```

## 🤝 Contribution

Les contributions sont les bienvenues ! 

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- APIs : CoinGecko, CoinMarketCap
- Librairies : NLTK, TA-Lib, Scikit-learn
- Communauté crypto open-source

---

Développé avec ❤️ pour la communauté crypto