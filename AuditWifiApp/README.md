# 🧠 Instructions pour l'Agent IA (Prompt System)

> Ces instructions sont destinées à l’IA qui m’assiste dans VS Code.
Je travaille sous PowerShell, pas bash. 
Tu es un assistant IA spécialisé en développement Python/CODESYS pour l’automatisation industrielle. Tu m’aides à construire une base de code robuste, modulaire et bien documentée.

- Chaque fonctionnalité doit être séparée dans son propre fichier ou module.
- Tu ne dois jamais modifier plusieurs modules si ce n’est pas nécessaire.
- Tu ne dois **jamais casser un module** en modifiant un autre.
- Si mes instructions sont floues, tu dois me poser des questions.
- Tu dois ajouter des commentaires clairs pour chaque fonction ou classe que tu écris.
- Tu n’utilises **aucune variable globale** sauf exception justifiée.
- Tu documentes ce que tu fais comme si un autre dev allait reprendre le projet.

Merci de suivre ces instructions à chaque modification du code.

# AuditWifiApp

## Objectif
Application destinée à réaliser des audits WiFi dans des usines où l'on souhaite implanter des AMR (robots mobiles autonomes). L'outil collecte et analyse des données réseau (RSSI, SNR, ping, position GPS, logs Moxa, etc.) pour identifier les zones à risque et améliorer le roaming WiFi.

## Configuration

### Variables d'environnement
L'application utilise des variables d'environnement pour stocker les configurations sensibles. Pour configurer l'application :

1. Copiez le fichier `.env.example` en `.env` :
   ```powershell
   Copy-Item .env.example .env
   ```

2. Modifiez le fichier `.env` avec vos propres valeurs :
   - `OPENAI_API_KEY` : Votre clé API OpenAI pour l'analyse des logs

Le fichier `.env` est ignoré par Git pour protéger vos informations sensibles. Ne commettez jamais ce fichier dans le dépôt.

## Fonctionnalités principales
- Collecte semi-automatique lors des déplacements sur le site (buggy équipé d’un portable, Moxa).
- Journalisation des mesures dans des fichiers CSV.
- Dépôt et analyse de logs Moxa pour suggestions d’amélioration du roaming.
- Alertes visuelles en temps réel lors de la détection de zones à risque (popup et changement de couleur).
- Notification sonore pour enregistrer manuellement la position.
- Possibilité de prendre des notes/commentaires sur la localisation.
- Paramétrage dynamique via `config.yaml`.
- Génération de rapports automatiques après la fin de l’audit.

## Structure du projet
```
├── api_errors.log             # Journal des erreurs API
├── config_manager.py          # Gestionnaire de configuration
├── config.yaml                # Configuration principale de l'application
├── wifi_monitor.ps1          # Script PowerShell pour la collecte WiFi en temps réel
├── src/
│   ├── ai/
│   │   ├── moxa_ai_analyzer.py    # Analyseur IA centralisé pour Moxa
│   │   ├── simple_moxa_analyzer.py # Analyseur simplifié pour Moxa
│   │   ├── simple_wifi_analyzer.py # Analyseur simplifié pour WiFi
│   │   └── wifi_ai_analyzer.py    # Analyseur IA centralisé pour WiFi
│   ├── moxa/
│   │   ├── analyzers/            # Analyseurs spécifiques Moxa
│   │   └── models/              # Modèles de données Moxa
│   └── wifi/
│       ├── analyzers/            # Analyseurs spécifiques WiFi
│       └── models/              # Modèles de données WiFi
├── log_manager.py             # Orchestrateur des analyseurs de logs
├── logger.py                  # Utilitaire de journalisation
├── moxa_analyzer.py           # Analyseur spécialisé pour les logs Moxa
├── network_scanner.py         # Scanner réseau
├── runner.py                  # Point d'entrée principal de l'application
├── wifi/wifi_analyzer.py      # Analyseur spécialisé pour les données WiFi
├── wifi_data_collector.py     # Collecteur de données WiFi
├── wifi_test_manager.py       # Gestionnaire des tests WiFi
├── archive/                   # Code archivé et anciennes versions
├── config/                    # Fichiers de configuration Moxa
├── logs/                      # Journaux d'analyse et fichiers CSV d'audit
└── logs_moxa/                 # Logs et résultats d'analyse Moxa
```

## Modules principaux
- **config_manager.py**: Gère le chargement, la sauvegarde et la réinitialisation des configurations.
- **log_manager.py**: Orchestrateur qui délègue les opérations d'analyse aux analyseurs spécialisés. Il reçoit les demandes d'analyse (WiFi ou Moxa), sélectionne le module d'analyse approprié, transmet les données à analyser, puis centralise et retourne les résultats à l'interface utilisateur.
- **wifi/wifi_analyzer.py**: Analyse spécifique des données WiFi. Il reçoit les échantillons collectés (RSSI, SNR, etc.), identifie les zones à risque (ex : faible signal, perte de paquets, congestion), et génère des recommandations. L'analyse se fait en fin de collecte ou à la demande.
- **moxa_analyzer.py**: Analyse des logs Moxa. Il traite les fichiers de logs déposés, extrait les événements pertinents (roaming, déconnexions, erreurs), puis propose des optimisations de configuration pour améliorer le roaming. Peut s'appuyer sur des sous-modules spécialisés (ex : moxa_log_analyzer, moxa_roaming_analyzer).
- **moxa_log_analyzer.py**: Analyse automatique des logs Moxa et génère des recommandations directes sur la configuration JSON (roaming_difference, max_transmission_power, rts_threshold, fragmentation_threshold, auth_timeout...). Les suggestions indiquent la valeur actuelle, la valeur proposée et la raison du changement.
- **wifi_monitor.ps1**: Script PowerShell qui collecte les données WiFi en temps réel. Il fournit des informations détaillées sur la connexion WiFi (RSSI, BSSID, canal, bande, etc.) et peut fonctionner en mode interactif (affichage en temps réel) ou en mode API (retourne les données en JSON).

- **wifi_data_collector.py**: Collecte les données WiFi en temps réel lors des déplacements sur le site. Utilise le script PowerShell wifi_monitor.ps1 pour obtenir des données précises. Les données sont stockées localement (CSV/logs) et transmises à l'analyseur WiFi à la fin du parcours ou sur demande.

- **wifi_test_manager.py**: Gère l'exécution des tests WiFi (démarrage, arrêt, état en cours). Il coordonne la collecte, assure la persistance des données, et déclenche l'analyse à la fin du test.
- **runner.py**: Point d'entrée principal et interface utilisateur. Il orchestre les modules : lance la collecte, déclenche les analyses, affiche les résultats (recommandations IA, alertes, logs bruts). Toutes les interactions utilisateur passent par ce module.

### Résumé du fonctionnement actuel de l'analyse

1. **Collecte des données** :
   - Le module `wifi_data_collector.py` enregistre en continu les mesures WiFi (RSSI, SNR, etc.) lors du déplacement sur le site.
   - Les logs Moxa sont déposés manuellement ou automatiquement dans le dossier dédié.

2. **Orchestration** :
   - L'utilisateur lance une analyse via l'interface (`runner.py`).
   - `runner.py` transmet la demande au `log_manager.py`, qui choisit l'analyseur adapté (WiFi ou Moxa).

3. **Analyse** :
  - L'analyseur (`wifi/wifi_analyzer.py` ou `moxa_analyzer.py`) traite les données reçues :
     - Pour le WiFi : détection des zones à risque, synthèse des métriques, génération de recommandations.
     - Pour Moxa : extraction des événements, analyse du roaming, suggestions d'optimisation.
   - Certains modules peuvent faire appel à l'IA (OpenAI) pour enrichir l'analyse (via les modules de la couche `src/ai/`).

4. **Restitution** :
   - Les résultats (recommandations, alertes, logs bruts) sont renvoyés à `runner.py` et affichés à l'utilisateur (fenêtre dédiée, alertes visuelles/sonores).

### Points d'amélioration possibles
- **Modularité accrue** : séparer davantage les sous-fonctions d'analyse (ex : analyse du roaming, analyse de la couverture) pour faciliter l'évolution.
- **Gestion des erreurs** : renforcer la robustesse face aux données incomplètes ou corrompues.
- **Interfaces plus explicites** : définir des API claires entre modules pour faciliter les tests et l'intégration de nouveaux analyseurs.
- **Tests unitaires** : ajouter des tests ciblés sur chaque analyseur pour garantir la stabilité lors des évolutions.

Ce résumé permet à un nouveau développeur de comprendre le flux global, les responsabilités de chaque module, et d'identifier rapidement où intervenir pour améliorer ou étendre l'analyse.

## Utilisation de l'API OpenAI

L'application utilise l'API OpenAI de manière simple et directe via deux points d'entrée :

1. **Analyse des logs Moxa** (`src/ai/simple_moxa_analyzer.py`):
   ```python
   from src.ai.simple_moxa_analyzer import analyze_moxa_logs

   # Les logs sont envoyés directement à OpenAI avec la config actuelle
   result = analyze_moxa_logs(logs_content, current_config)
   # result contient la réponse brute d'OpenAI avec l'analyse
   ```

2. **Analyse des données WiFi** (`src/ai/simple_wifi_analyzer.py`):
   ```python
   from src.ai.simple_wifi_analyzer import analyze_wifi_data

   # À la fin du test WiFi, on envoie toutes les données collectées
   result = analyze_wifi_data(collected_wifi_data)
   # result contient la réponse brute d'OpenAI avec l'analyse
   ```

La réponse d'OpenAI est affichée directement dans l'interface, sans traitement supplémentaire. Cela permet une lecture facile des recommandations et une meilleure compréhension du raisonnement de l'IA.

### Configuration de la clé API

Créez un fichier `.env` à la racine du projet pour stocker la clé API :

```dotenv
OPENAI_API_KEY=votre-cle
```

Ce fichier est ignoré par Git. L'application charge automatiquement cette valeur avec `python-dotenv`.

Le fichier `config/api_config.json` n'est plus utilisé et peut être ignoré.

## Questions pour clarifier le besoin

1. **Concernant l'intégration avec l'API OpenAI:**
   - Quelles limites de tokens/requêtes faut-il respecter? 8000
   - Avez-vous besoin de gérer le contexte des conversations précédentes? non

2. **Concernant la collecte de données Wi-Fi:**
   - À quelle fréquence les données doivent-elles être collectées? celon une bonne pratique pour teste de la couverture wifi, je vais marcher avec un bugey dans toute l'usine
   - Quels seuils définissent une "zone à risque"? une zone ou je risque d'etre déconnecter du wifi, ou bien perte de paquet élever.. ou si beaucoup de traffic sur une antenne.

3. **Concernant les AMR (robots mobiles):**
   - Quels sont les critères spécifiques de stabilité Wi-Fi pour vos AMR? le roaming est le plus grand enjeux avec les deconection et la force du signal.
   - Quelles métriques sont les plus critiques pour le fonctionnement des AMR? roaming et deconnection

4. **Concernant l'analyse des logs Moxa:**
   - Y a-t-il des paramètres de configuration Moxa prioritaires à optimiser? ceux fournis dans mes config
   - Comment voulez-vous visualiser les résultats de l'analyse? dans une fenetre a droite de l'ecran

5. **Concernant la génération de rapports:**
   - Quel format de rapport souhaitez-vous (PDF, HTML, autre)? peu importe en texte
   - Quelles informations doivent absolument figurer dans ces rapports? le rapport fais par ia et le log en dessous

6. **Concernant le déploiement:**
   - L'application sera-t-elle exécutée sur des ordinateurs portables sur le terrain? oui
   - Y a-t-il des contraintes matérielles ou logicielles spécifiques? non


## bonne pratique a suivre

Contexte : Je développe une application avec plusieurs fonctionnalités.
Problème : Quand je modifie une partie du code, une autre se brise.
Objectif : Séparer proprement les responsabilités pour éviter les effets de bord.
Consignes :
   1. Modularise le code : chaque fonction ou module doit faire une seule chose (principe de responsabilité unique).
   2. Encapsule les données et les comportements dans des classes ou des modules isolés (évite les dépendances croisées).
   3. N’utilise pas de variables globales partagées entre modules (utilise des paramètres ou des services injectables).
   4. Ajoute une interface claire entre les modules pour qu’ils ne se parlent qu’à travers une API définie.
   5. Si tu ajoutes une fonctionnalité, crée un fichier ou un module dédié au lieu de modifier du code existant.
   6. Commente chaque fonction pour décrire ce qu’elle fait et ses dépendances.
   7. Teste chaque module indépendamment avec des fonctions d’essai ou des mocks.




   🧠 Utiliser l'IA pour des projets complexes : bonnes pratiques
      1. Définir une architecture modulaire : Découpe ton application en modules ou composants indépendants, chacun responsable d'une fonctionnalité spécifique. Cela facilite la maintenance et réduit les risques d'effets de bord lors des modifications.
      2. Utiliser des interfaces claires : Chaque module devrait exposer des interfaces bien définies pour interagir avec les autres. Cela permet de modifier l'implémentation interne sans impacter les autres parties du système.
      3. Adopter des conventions de nommage cohérentes : Des noms de fichiers, classes et fonctions explicites facilitent la compréhension du code, tant pour toi que pour l'agent IA.
      4. Documenter le code : Inclure des commentaires et une documentation détaillée aide l'IA à mieux comprendre le contexte et à générer du code plus pertinent.
      5. Écrire des tests automatisés : Les tests unitaires et d'intégration permettent de détecter rapidement les régressions et assurent la stabilité de l'application lors des évolutions.
Utiliser un système de contrôle de version : Git, par exemple, permet de suivre les modifications, de collaborer efficacement et de revenir à des versions antérieures en cas de besoin.

## Tests Automatiques

Les tests automatiques sont organisés en deux modules principaux :

### 1. Tests de l'Analyseur Moxa

Les tests pour l'analyseur Moxa couvrent :
- L'analyse basique des logs Moxa
- La gestion des logs vides ou invalides
- L'intégration avec le LogManager
- L'intégration avec l'interface utilisateur

### 2. Tests de l'Analyseur WiFi

Les tests pour l'analyseur WiFi couvrent :
- La collecte de données WiFi
- L'analyse des données collectées
- La gestion des tests WiFi via le WifiTestManager
- L'intégration avec l'interface utilisateur
- La gestion des données invalides
- La persistance des données (sauvegarde/chargement)

### Exécution des tests

Pour exécuter les tests, utilisez la commande suivante :

```bash
pytest -v
```

Pour générer un rapport de couverture des tests :

```bash
pytest --cov=. --cov-report=term
```

Un rapport détaillé des tests est disponible dans le fichier `TEST_SUMMARY.md`.

