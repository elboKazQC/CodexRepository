# 🤖 Guide Complet - Onglet Monitoring AMR

## 🎯 Aperçu de l'Onglet
L'onglet **Monitoring AMR** est spécialement conçu pour surveiller en temps réel les robots mobiles autonomes (AMR) déployés en environnement industriel. Il permet de monitorer leur connectivité réseau, détecter les problèmes de communication et optimiser leurs performances opérationnelles.

## 🚀 Fonctionnalités Principales

### 📡 Surveillance Multi-AMR
- **Monitoring simultané** de plusieurs AMR
- **Surveillance en temps réel** de la connectivité
- **Détection automatique** des problèmes réseau
- **Historique de performance** pour chaque AMR
- **Alertes proactives** en cas de dysfonctionnement

### 🎮 Contrôles Disponibles

#### Gestion des Adresses IP
- **Zone de saisie** : Ajout d'adresses IP d'AMR
- **Bouton Ajouter** : Inclusion dans la liste de surveillance
- **Bouton Supprimer** : Retrait d'AMR de la surveillance
- **Liste des AMR** : Affichage de tous les robots surveillés

#### Contrôles de Monitoring
- **▶ Démarrer** : Lance la surveillance en continu
- **⏹ Arrêter** : Stoppe le monitoring
- **Traceroute** : Diagnostic réseau approfondi pour l'AMR sélectionné

### 📊 Métriques Surveillées

#### Connectivité de Base
- **Ping Response** : Temps de réponse de chaque AMR
- **Availability** : Pourcentage de disponibilité
- **Packet Loss** : Taux de perte de paquets
- **Jitter** : Stabilité de la connexion

#### Indicateurs Visuels
- **📡 AMR En Ligne** : Connexion normale (vert)
- **🔵 AMR Détecté** : Communication établie (bleu)
- **🔴 AMR Hors Ligne** : Perte de connexion (rouge)
- **⚠️ AMR Instable** : Connexion intermittente (orange)

### 🔍 Diagnostic Avancé

#### Traceroute Intégré
- **Chemin réseau complet** vers l'AMR
- **Identification des goulots** d'étranglement
- **Temps de réponse** par hop
- **Détection des points** de défaillance

#### Analyse de Performance
- **Tendances de latence** sur période
- **Patterns de déconnexion** récurrents
- **Corrélation** avec événements réseau
- **Recommandations d'optimisation**

## 🎯 Guide d'Utilisation Pratique

### 🏗️ Configuration Initiale

#### Ajout d'AMR
1. **Obtenir les adresses IP** des AMR depuis leur interface
2. **Saisir l'adresse** dans le champ dédié
3. **Cliquer "Ajouter"** pour inclure dans la surveillance
4. **Répéter** pour tous les AMR de la flotte

#### Démarrage du Monitoring
1. **Vérifier la liste** des AMR configurés
2. **Cliquer "▶ Démarrer"** pour lancer la surveillance
3. **Observer les indicateurs** de statut en temps réel
4. **Analyser les métriques** dans le panneau de droite

### 🔧 Opérations de Maintenance

#### Surveillance Quotidienne
- **Vérification matinale** : Status de tous les AMR
- **Monitoring continu** : Alertes en temps réel
- **Contrôle de fin** : Bilan de journée
- **Archivage des logs** : Conservation historique

#### Diagnostic de Problème
1. **Identifier l'AMR** problématique (indicateur rouge/orange)
2. **Sélectionner dans la liste** l'AMR concerné
3. **Lancer "Traceroute"** pour diagnostic approfondi
4. **Analyser le chemin réseau** et les points de latence
5. **Appliquer les corrections** nécessaires

### 🎬 Analyse Prédictive

#### Patterns de Performance
- **Surveillance des tendances** de latence
- **Détection de dégradation** progressive
- **Identification des heures** de pointe
- **Corrélation avec charge** industrielle

#### Maintenance Préventive
- **Alertes anticipées** avant défaillance
- **Planning de maintenance** optimisé
- **Prévention des arrêts** de production
- **Optimisation des ressources** réseau

## 🔧 Configuration et Paramétrage

### Seuils d'Alerte
- **Ping timeout** : > 1000 ms (1 seconde)
- **Perte de paquets** : > 5%
- **Jitter excessif** : > 100 ms
- **Disponibilité minimale** : < 95%

### Intervalles de Surveillance
- **Ping frequency** : Toutes les 5 secondes
- **Status update** : Toutes les 10 secondes
- **Log rotation** : Quotidienne
- **Report generation** : Hebdomadaire

### Types d'AMR Supportés
- **AGV classiques** : Support IP standard
- **AMR autonomes** : Protocoles avancés
- **Robots collaboratifs** : Surveillance spécialisée
- **Équipements IoT** : Monitoring étendu

## 📊 Métriques et KPIs

### Indicateurs de Performance
- **Uptime** : Pourcentage de disponibilité
- **MTBF** : Temps moyen entre pannes
- **MTTR** : Temps moyen de réparation
- **Efficiency** : Taux d'efficacité opérationnelle

### Métriques Réseau
- **RTT moyen** : Temps de réponse typique
- **Packet loss rate** : Taux de perte
- **Bandwidth utilization** : Utilisation bande passante
- **Connection stability** : Stabilité de connexion

### Alertes Configurables
- **AMR déconnecté** : Perte de communication
- **Latence élevée** : Dégradation performance
- **Jitter important** : Instabilité réseau
- **Perte de paquets** : Problème infrastructure

## 🚨 Résolution de Problèmes

### AMR Non Responsive
**Symptômes** : Aucune réponse aux ping
**Diagnostic** :
1. Vérifier l'alimentation de l'AMR
2. Contrôler la connectivité WiFi physique
3. Vérifier la configuration IP
4. Tester la connectivité locale

**Solutions** :
- Redémarrage de l'AMR
- Reconfiguration réseau
- Vérification des points d'accès
- Contrôle des interférences

### Latence Élevée
**Symptômes** : Temps de réponse > 100 ms
**Diagnostic** :
1. Lancer un traceroute détaillé
2. Identifier les goulots d'étranglement
3. Analyser la charge réseau
4. Vérifier la configuration QoS

**Solutions** :
- Optimisation des routes réseau
- Mise à niveau de l'infrastructure
- Configuration de priorités QoS
- Réduction du trafic concurrent

### Connexions Instables
**Symptômes** : Déconnexions/reconnexions fréquentes
**Diagnostic** :
1. Analyser les patterns de déconnexion
2. Vérifier la couverture WiFi
3. Contrôler les interférences
4. Examiner les logs AMR

**Solutions** :
- Optimisation du roaming WiFi
- Ajout de points d'accès
- Réduction des interférences
- Mise à jour firmware AMR

### Pertes de Paquets
**Symptômes** : Packet loss > 5%
**Diagnostic** :
1. Identifier la source des pertes
2. Analyser la qualité du signal
3. Vérifier la congestion réseau
4. Contrôler les équipements

**Solutions** :
- Amélioration de la couverture
- Optimisation des canaux
- Mise à niveau équipements
- Configuration de buffers

## 💡 Optimisations Recommandées

### Pour l'Infrastructure
- **Redondance réseau** : Chemins multiples
- **QoS prioritaire** : Trafic AMR prioritaire
- **Monitoring proactif** : Surveillance 24/7
- **Maintenance préventive** : Planning optimisé

### Pour les AMR
- **Configuration optimale** : Paramètres réseau
- **Mise à jour régulière** : Firmware et logiciels
- **Surveillance continue** : Monitoring intégré
- **Backup de configuration** : Sauvegarde paramètres

### Pour l'Équipe
- **Formation** : Utilisation des outils
- **Procédures** : Actions standardisées
- **Documentation** : Maintien à jour
- **Support** : Équipe dédiée

## 📈 Rapports et Analytics

### Rapports Quotidiens
- **Status global** de la flotte
- **Incidents** de la journée
- **Performance metrics** détaillées
- **Actions recommandées**

### Rapports Hebdomadaires
- **Tendances** de performance
- **Analyse comparative** inter-AMR
- **Recommandations d'optimisation**
- **Planning de maintenance**

### Analytics Avancés
- **Prédiction de pannes** basée sur l'IA
- **Optimisation automatique** de routes
- **Corrélation** avec données production
- **ROI** du monitoring

Cet onglet est essentiel pour maintenir une flotte d'AMR performante et fiable en environnement industriel, garantissant la continuité opérationnelle et l'optimisation des investissements.
