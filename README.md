# Veille Crypto Twitter

Un script Python pour automatiser la veille d'information crypto sur Twitter.

## Fonctionnalités

- Récupération automatique des derniers tweets de comptes crypto sélectionnés
- Filtrage des retweets et des tweets sponsorisés
- Génération de résumés intelligents par compte
- Analyse des hashtags et de l'engagement
- Export des résultats en JSON
- Affichage console formaté
- Connexion automatique à Twitter pour un accès amélioré

## Prérequis

- Python 3.8+
- Chrome ou Firefox installé sur votre système
- Accès à Internet stable
- Compte Twitter (pour un accès optimal)

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

4. Configuration du compte Twitter :
   - Modifiez le fichier `config.py` pour ajouter vos identifiants Twitter
   - Les identifiants sont utilisés pour un accès amélioré aux tweets

## Configuration

Les comptes à surveiller sont configurés dans `config.py`. Vous pouvez modifier la liste `CRYPTO_ACCOUNTS` pour ajouter ou retirer des comptes.

## Utilisation

Exécutez le script principal :
```bash
python main.py
```

Le script va :
1. Se connecter automatiquement à Twitter
2. Récupérer les tweets de tous les comptes configurés
3. Générer des résumés intelligents
4. Afficher les résultats dans la console
5. Sauvegarder les résultats dans un fichier JSON

## Structure du Projet

- `main.py` : Point d'entrée du script
- `twitter_fetcher.py` : Gestion de la récupération des tweets via Selenium
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

## Limitations

- Respect des limites de Twitter (rate limiting)
- Temps de chargement des pages
- Nécessité d'un navigateur installé
- Possibilité de détection par Twitter
- Nécessité d'un compte Twitter pour un accès optimal

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