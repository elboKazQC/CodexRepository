# Moxa WiFi Analyzer

## Objectif
Une extension VS Code pour analyser les logs de configuration WiFi des appareils Moxa et générer des recommandations personnalisées à l'aide de l'IA. Cette extension est particulièrement utile pour optimiser les configurations WiFi dans des environnements industriels où des robots mobiles autonomes (AMR) sont déployés.

## Fonctionnalités principales
- Analyse avancée des logs Moxa par intelligence artificielle
- Interface utilisateur intuitive intégrée à VS Code
- Recommandations personnalisées pour améliorer les performances de roaming
- Suggestions détaillées de modifications de configuration avec justifications
- Métriques détaillées sur les performances de roaming (temps de basculement, SNR, etc.)
- Exportation des rapports d'analyse au format JSON ou texte

## Utilisation
1. Ouvrez l'extension via l'icône Moxa WiFi Analyzer dans la barre d'activités
2. Configurez les paramètres de votre appareil Moxa dans l'onglet "Configuration"
3. Importez vos logs Moxa dans l'onglet "Logs Analysis"
4. Examinez les recommandations et métriques de performance dans l'onglet "Recommendations"
5. Appliquez les changements suggérés et exportez les rapports

## Paramètres analysés
- Taux de transmission minimum
- Puissance de transmission maximale
- Seuil RTS
- Seuil de fragmentation
- Mécanisme de roaming (SNR ou force du signal)
- Différence de roaming
- Seuils de roaming
- Vérification de connexion distante
- WMM (Wi-Fi Multimedia)
- Turbo Roaming
- AP Alive Check

## Prérequis
- Visual Studio Code 1.80.0 ou supérieur
- Clé API OpenAI (peut être configurée dans les paramètres de l'extension)

## Structure du projet
- src/extension.ts : Point d'entrée principal de l'extension
- src/moxaAnalyzer.ts : Logique d'analyse des logs et génération des recommandations
- src/configurationViewProvider.ts : Interface de configuration des paramètres Moxa
- src/logsViewProvider.ts : Interface d'analyse des logs
- src/recommendationsViewProvider.ts : Interface de présentation des recommandations
- resources/ : Ressources graphiques pour l'extension

## Configuration
L'extension permet de configurer les paramètres suivants:
- `moxaWifiAnalyzer.openaiApiKey`: Votre clé API OpenAI pour l'analyse des logs
- `moxaWifiAnalyzer.aiModel`: Le modèle d'IA à utiliser pour l'analyse (par défaut: "gpt-4o")
