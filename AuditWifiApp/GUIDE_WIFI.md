# 📡 Guide Complet - Onglet Analyse WiFi

## 🎯 Aperçu de l'Onglet
L'onglet **Analyse WiFi** est le cœur de l'application pour l'audit et l'analyse en temps réel des réseaux WiFi. Il permet de collecter, analyser et visualiser les performances WiFi pour optimiser l'implantation d'AMR (Autonomous Mobile Robots) en environnement industriel.

## 🚀 Fonctionnalités Principales

### 📊 Collecte de Données en Temps Réel
- **Démarrage/Arrêt** : Contrôle simple de la collecte de données WiFi
- **Signal RSSI** : Mesure de la force du signal en dBm
- **Latence** : Mesure des temps de ping vers les points d'accès
- **Jitter** : Analyse de la stabilité de la connexion
- **Débit** : Mesure des vitesses de transmission

### 🎮 Contrôles Disponibles

#### Boutons de Base
- **▶ Démarrer l'analyse** : Lance la collecte des données WiFi
- **⏹ Arrêter l'analyse** : Stoppe la collecte et analyse les données
- **🗂 Gérer les MAC** : Gestion des adresses MAC avec étiquetage

#### Navigation Temporelle
- **⏮️ Début** : Va au début de l'historique
- **⏭️ Fin/Live** : Retourne au mode temps réel
- **📈 Meilleur signal** : Navigue vers les pics de signal
- **📉 Signal faible** : Localise les zones de signal faible
- **🚨 Alertes** : Navigation entre les événements critiques

#### Options d'Affichage
- **📡 Suivi Direct** : Mode temps réel pour monitoring live
- **📊 Analyse** : Mode navigation pour analyse historique
- **🖥️ Plein Écran** : Interface dédiée pour présentations

### 📈 Graphiques et Visualisations

#### Graphique Principal (Signal WiFi)
- **Courbe bleue** : Force du signal RSSI en dBm
- **Marqueurs rouges** : Alertes de signal faible (< -70 dBm)
- **Zone verte** : Signal excellent (> -50 dBm)
- **Zone orange** : Signal moyen (-50 à -70 dBm)
- **Zone rouge** : Signal faible (< -70 dBm)

#### Graphique de Latence
- **Courbe orange** : Temps de ping en millisecondes
- **Seuil d'alerte** : > 100ms (marqué en rouge)
- **Évolution temporelle** : Tendances et pics de latence

#### Graphique de Jitter
- **Courbe magenta** : Variation de la latence
- **Stabilité** : Valeurs faibles = connexion stable
- **Instabilité** : Pics = problèmes de réseau

### 📋 Onglets d'Analyse Détaillée

#### 🚨 Alertes
- **Événements critiques** automatiquement détectés
- **Horodatage** précis de chaque alerte
- **Type d'alerte** : Signal faible, latence élevée, perte de connexion
- **Recommendations** automatiques pour résolution

#### 📋 Historique
- **Journal complet** de toutes les mesures
- **Export possible** en CSV pour analyse externe
- **Filtrage** par période et type d'événement

#### 📊 Stats Avancées
- **Moyennes** et médianes des métriques
- **Percentiles** (90%, 95%, 99%)
- **Analyse de tendance** et corrélations
- **Recommandations d'optimisation**

#### 📋 Rapport Final
- **Synthèse complète** de l'audit
- **Zones problématiques** identifiées
- **Plan d'amélioration** recommandé
- **Export professionnel** possible

## 🎯 Guide d'Utilisation Pratique

### 🏗️ Audit d'Implantation AMR

#### Phase 1 : Préparation
1. **Planifier le parcours** : Définir les zones à auditer
2. **Configurer l'équipement** : Vérifier la connectivité
3. **Lancer l'analyse** : Cliquer sur "▶ Démarrer l'analyse"

#### Phase 2 : Collecte
1. **Déplacement méthodique** dans les zones de travail
2. **Marquage des positions** critiques
3. **Surveillance en temps réel** des métriques
4. **Arrêt de l'analyse** après couverture complète

#### Phase 3 : Analyse
1. **Mode Analyse** : Basculer depuis "Suivi Direct"
2. **Navigation temporelle** : Examiner les zones problématiques
3. **Analyse des alertes** : Identifier les causes
4. **Génération du rapport** final

### 🎬 Présentation Client

#### Préparation
1. **Mode Plein Écran** : Pour visibilité maximale
2. **Navigation préparée** : Repérer les événements clés
3. **Données de démo** : Utiliser `launch_demo.py` si nécessaire

#### Démonstration
1. **Vue d'ensemble** : Montrer l'historique complet
2. **Zoom sur problèmes** : Naviguer vers les alertes
3. **Comparaison avant/après** : Utiliser les contrôles temporels
4. **Export de preuves** : Captures d'écran via toolbar

## 🔧 Paramètres et Configuration

### Seuils d'Alerte
- **Signal faible** : < -70 dBm (configurable)
- **Latence élevée** : > 100 ms
- **Perte de paquets** : > 5%
- **Jitter excessif** : > 50 ms

### Fenêtres d'Affichage
- **50 échantillons** : Analyse fine (5 min)
- **100 échantillons** : Vue détaillée (10 min)
- **200 échantillons** : Vue étendue (20 min)
- **500 échantillons** : Vue large (50 min)
- **Total** : Historique complet

### Options d'Export
- **CSV** : Données brutes pour analyse externe
- **PNG/PDF** : Graphiques pour rapports
- **Rapport HTML** : Document complet avec recommandations

## 💡 Conseils d'Optimisation

### Pour Environnement Industriel
- **Fréquence 5 GHz** préférée (moins encombrée)
- **Points d'accès dédiés** pour AMR si possible
- **Canaux non-overlapping** (1, 6, 11 en 2.4 GHz)
- **Puissance adaptée** pour éviter interférences

### Pour AMR
- **Signal minimum** : -65 dBm recommandé
- **Latence cible** : < 50 ms pour réactivité
- **Couverture redondante** : Overlap 20-30%
- **Roaming rapide** : Paramètres optimisés

### Analyse des Résultats
- **Zones mortes** : Signal < -80 dBm = implantation AP
- **Interférences** : Jitter élevé = changement de canal
- **Latence** : > 100 ms = problème réseau/infrastructure
- **Instabilité** : Roaming mal configuré

## 🚨 Résolution de Problèmes

### Signal Faible
- **Cause** : Distance excessive ou obstacles
- **Solution** : Ajouter des points d'accès ou repositionner

### Latence Élevée
- **Cause** : Congestion réseau ou configuration
- **Solution** : Optimiser QoS, changer de canal

### Jitter Important
- **Cause** : Interférences ou surcharge
- **Solution** : Identifier sources d'interférence

### Pertes de Connexion
- **Cause** : Roaming mal configuré
- **Solution** : Ajuster seuils de roaming

## 📊 Métriques de Référence

### Signal WiFi (RSSI)
- **Excellent** : > -50 dBm
- **Bon** : -50 à -60 dBm
- **Correct** : -60 à -70 dBm
- **Faible** : -70 à -80 dBm
- **Très faible** : < -80 dBm

### Latence
- **Excellente** : < 10 ms
- **Bonne** : 10-50 ms
- **Correcte** : 50-100 ms
- **Élevée** : > 100 ms

### Jitter
- **Stable** : < 10 ms
- **Acceptable** : 10-30 ms
- **Instable** : > 30 ms

Cet onglet constitue l'outil principal pour garantir une connectivité WiFi optimale pour vos AMR en environnement industriel.
