# Veille Crypto

Un outil de veille crypto qui agrège des données de différentes sources.

## Fonctionnalités

- Récupération des prix des cryptos depuis CoinGecko
- Analyse de sentiment depuis CryptoPanic RSS
- Articles de news depuis plusieurs sources RSS (CoinDesk, CoinTelegraph, CryptoNews)
- Posts Reddit depuis les subreddits crypto populaires
- Tweets crypto depuis Twitter (via scraping)

## Prérequis

- Python 3.8+
- Chrome/Chromium installé
- ChromeDriver installé et configuré

## Installation

1. Clonez le repository :
```bash
git clone https://github.com/votre-username/veille_crypto.git
cd veille_crypto
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurez les variables d'environnement :
```bash
cp .env.example .env
# Éditez le fichier .env avec vos configurations
```

## Configuration

### Variables d'environnement

- `TWITTER_API_KEY` : Clé API Twitter
- `TWITTER_API_SECRET` : Secret API Twitter
- `TWITTER_ACCESS_TOKEN` : Token d'accès Twitter
- `TWITTER_ACCESS_TOKEN_SECRET` : Secret du token d'accès Twitter
- `CHROMEDRIVER_PATH` : Chemin vers l'exécutable ChromeDriver
- `COINGECKO_API_KEY` : Clé API CoinGecko (optionnelle)
- `DATA_DIR` : Dossier de stockage des données
- `LOGS_DIR` : Dossier de stockage des logs

### ChromeDriver

Le script nécessite ChromeDriver pour le scraping Twitter. Vous pouvez :
1. Télécharger ChromeDriver manuellement depuis [le site officiel](https://sites.google.com/chromium.org/driver/)
2. Placer l'exécutable dans un dossier de votre PATH
3. Ou spécifier son chemin dans la variable d'environnement `CHROMEDRIVER_PATH`

## Utilisation

### Récupération des données

```bash
python main.py
```

Options disponibles :
- `--skip-market` : Ne pas récupérer les données de marché
- `--skip-external` : Ne pas récupérer les données externes

### Tests

```bash
python -m pytest tests/
```

## Structure du projet

```
veille_crypto/
├── data/                  # Dossier de stockage des données
├── logs/                  # Dossier de stockage des logs
├── src/                   # Code source
│   ├── market_data_fetcher.py    # Récupération des données de marché
│   ├── external_sources_fetcher.py    # Récupération des sources externes
│   ├── twitter_fetcher.py        # Récupération des tweets
│   ├── utils.py                  # Utilitaires
│   └── main.py                   # Point d'entrée
├── tests/                 # Tests
├── .env.example           # Exemple de configuration
├── requirements.txt       # Dépendances
└── README.md             # Documentation
```

## Sources de données

### Données de marché
- CoinGecko API (gratuite)
- CryptoPanic RSS (gratuit)

### Sources externes
- CoinDesk RSS (gratuit)
- CoinTelegraph RSS (gratuit)
- CryptoNews RSS (gratuit)
- Reddit API (gratuite)
- Twitter (via scraping)

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 