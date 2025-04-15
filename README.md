# Veille Crypto

Un outil de veille automatisée pour suivre l'actualité crypto sur Twitter et les marchés.

## Fonctionnalités

- Récupération automatique des tweets des comptes crypto majeurs
- Analyse des thèmes et tendances
- Suivi des données de marché (prix, volume, etc.)
- Alertes de baleines
- Métriques de sentiment
- Sources d'actualités externes
- Système de cache intelligent
- Tests unitaires complets

## Installation

1. Cloner le repository :
```bash
git clone https://github.com/votre-username/veille_crypto.git
cd veille_crypto
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Éditer .env avec vos identifiants
```

## Configuration

Le fichier `.env` doit contenir :
```
TWITTER_USERNAME=votre_username
TWITTER_PASSWORD=votre_password
COINGECKO_API_KEY=votre_clé_api
GLASSNODE_API_KEY=votre_clé_api
WHALE_ALERT_API_KEY=votre_clé_api
CRYPTOPANIC_API_KEY=votre_clé_api
```

## Utilisation

### Récupération complète
```bash
python main.py
```

### Récupération des données de marché uniquement
```bash
python main.py --market-only
```

## Tests

Pour exécuter les tests :
```bash
python -m unittest discover tests
```

## Structure du Projet

```
veille_crypto/
├── .env                    # Variables d'environnement
├── .env.example           # Exemple de configuration
├── .gitignore            # Fichiers à ignorer
├── config.py             # Configuration
├── external_sources_fetcher.py  # Sources externes
├── main.py               # Point d'entrée
├── market_data_fetcher.py # Données de marché
├── requirements.txt      # Dépendances
├── summarizer.py         # Analyse des tweets
├── tests/               # Tests unitaires
│   ├── __init__.py
│   ├── test_summarizer.py
│   └── test_twitter_fetcher.py
└── twitter_fetcher.py    # Récupération des tweets
```

## Améliorations Récentes

- Optimisation de la récupération des tweets
- Système de cache intelligent avec TTL
- Analyse améliorée des thèmes
- Tests unitaires complets
- Gestion robuste des erreurs
- Documentation améliorée

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 