# Veille Crypto Twitter

Un script Python pour automatiser la veille d'information crypto sur Twitter et les données de marché.

## Fonctionnalités

- Récupération automatique des derniers tweets de comptes crypto sélectionnés
- Filtrage des retweets et des tweets sponsorisés
- Génération de résumés intelligents par compte
- Analyse des hashtags et de l'engagement
- Récupération des données de marché (prix, alertes de baleines, métriques de sentiment)
- Intégration de sources externes (régulation, exchanges, communautés)
- Export des résultats en JSON
- Affichage console formaté
- Connexion automatique à Twitter pour un accès amélioré

## Sources d'Information

### Twitter
- Tweets des comptes crypto configurés
- Filtrage des retweets et tweets sponsorisés
- Analyse des hashtags et de l'engagement

### Données de Marché
- Prix des cryptos via CoinGecko
- Alertes de baleines via Whale Alert
- Métriques de sentiment via Glassnode

### Sources Externes
#### Régulation & Institutions
- SEC News (RSS)
- CFTC (RSS)
- ESMA (RSS)
- BCE (Scraping)
- IMF (RSS)

#### Exchanges
- Binance Blog (RSS)
- Coinbase Newsroom (RSS)

#### Communautés & News
- CryptoPanic (API)
- Google Trends
- Hackernoon (RSS)
- Bitcointalk (Scraping)

## Prérequis

- Python 3.8+
- Chrome ou Firefox installé sur votre système
- Accès à Internet stable
- Compte Twitter (pour un accès optimal)
- Clés API pour les services de données de marché (optionnel)

## Installation

1. Clonez le repository :
```bash
git clone [URL_DU_REPO]
cd veille_crypto
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Installation de Chrome/ChromeDriver :
   - Le script utilise Chrome en mode headless
   - ChromeDriver est automatiquement installé via webdriver-manager
   - Assurez-vous d'avoir Chrome installé sur votre système

4. Configuration des API :
   - Copiez `.env.example` vers `.env`
   - Ajoutez vos identifiants Twitter et clés API dans `.env`
   - Les clés API sont optionnelles mais recommandées pour un accès optimal

## Configuration

Les comptes à surveiller sont configurés dans `config.py`. Vous pouvez modifier la liste `CRYPTO_ACCOUNTS` pour ajouter ou retirer des comptes.

## Utilisation

Exécutez le script principal :
```bash
python main.py
```

Options disponibles :
```bash
python main.py --market-only  # Récupérer uniquement les données de marché
python main.py --external-only  # Récupérer uniquement les sources externes
```

Le script va :
1. Se connecter automatiquement à Twitter
2. Récupérer les tweets de tous les comptes configurés
3. Récupérer les données de marché (prix, alertes, sentiment)
4. Récupérer les sources externes (régulation, exchanges, communautés)
5. Générer des résumés intelligents
6. Afficher les résultats dans la console
7. Sauvegarder les résultats dans un fichier JSON

## Structure du Projet

- `main.py` : Point d'entrée du script
- `twitter_fetcher.py` : Gestion de la récupération des tweets via Selenium
- `market_data_fetcher.py` : Récupération des données de marché
- `external_sources_fetcher.py` : Récupération des sources externes
- `summarizer.py` : Génération des résumés
- `config.py` : Configuration et paramètres
- `requirements.txt` : Dépendances du projet

## Gestion des Erreurs

Le script inclut :
- Gestion des erreurs de chargement de page
- Système de retry automatique
- Logging détaillé des opérations
- Gestion des timeouts et des éléments non trouvés
- Gestion des erreurs de connexion à Twitter
- Gestion des erreurs d'API de données de marché
- Gestion des erreurs de flux RSS et de scraping

## Limitations

- Respect des limites de Twitter (rate limiting)
- Temps de chargement des pages
- Nécessité d'un navigateur installé
- Possibilité de détection par Twitter
- Nécessité d'un compte Twitter pour un accès optimal
- Limites des APIs gratuites de données de marché
- Disponibilité des flux RSS et des sources externes

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Notes Techniques

### Sélecteurs Utilisés

Le script utilise les sélecteurs XPath suivants pour extraire les données :
- Texte du tweet : `//div[@data-testid='tweetText']`
- Date : `//time`
- Métriques : `//div[@data-testid='like']//span`
- Hashtags : `//a[contains(@href, '/hashtag/')]`

### Optimisations

- Mode headless pour Chrome
- Désactivation des images
- User-Agent aléatoire
- Délais aléatoires entre les actions
- Gestion des timeouts
- Connexion automatique à Twitter
- Mise en cache des données de marché
- Limitation du nombre d'entrées RSS

### Format de Sortie JSON

```json
{
  "timestamp": "2024-03-31T12:00:00",
  "tweets": {
    "account_name": {
      "summary": "...",
      "hashtags": ["...", "..."],
      "engagement": 123.4
    }
  },
  "market": {
    "prices": {
      "source": "coingecko",
      "timestamp": "...",
      "prices": {
        "bitcoin": 66421.32,
        "ethereum": 3324.56
      },
      "changes_24h": {
        "bitcoin": -2.1,
        "ethereum": 1.5
      }
    },
    "whale_alerts": [
      {
        "source": "whale_alert",
        "timestamp": "...",
        "amount_usd": 500000,
        "currency": "BTC"
      }
    ],
    "sentiment": {
      "source": "glassnode",
      "timestamp": "...",
      "metrics": {
        "fear_and_greed": 65,
        "nvt": 123.45
      }
    }
  },
  "external_sources": {
    "timestamp": "...",
    "regulatory": [
      {
        "source": "sec",
        "title": "...",
        "link": "...",
        "published": "...",
        "summary": "..."
      }
    ],
    "exchanges": [
      {
        "source": "binance",
        "title": "...",
        "link": "...",
        "published": "...",
        "summary": "..."
      }
    ],
    "community": [
      {
        "source": "hackernoon",
        "title": "...",
        "link": "...",
        "published": "...",
        "summary": "..."
      }
    ],
    "trends": {
      "source": "google_trends",
      "keywords": ["bitcoin", "ethereum", "cryptocurrency"],
      "data": {
        "bitcoin": [100, 95, 105, ...],
        "ethereum": [80, 85, 75, ...]
      }
    },
    "news": [
      {
        "source": "cryptopanic",
        "title": "...",
        "url": "...",
        "published_at": "...",
        "source_title": "...",
        "sentiment": "positive"
      }
    ]
  }
}
``` 