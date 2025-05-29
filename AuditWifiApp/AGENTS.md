# AGENTS - Documentation des Assistants IA

Ce document décrit les différents agents et assistants IA utilisés dans le projet **AuditWifiApp** pour l'analyse et le monitoring réseau WiFi.

## 🤖 Vue d'ensemble

L'application utilise plusieurs types d'agents spécialisés pour automatiser l'analyse, le diagnostic et la génération de rapports réseau.

## 📋 Types d'Agents

### 1. Agent d'Analyse Réseau Principal
- **Rôle** : Collecte et analyse en temps réel des données WiFi
- **Fonctionnalités** :
  - Surveillance continue de la qualité du signal
  - Détection automatique des anomalies
  - Calcul des métriques de performance
  - Génération d'alertes intelligentes

### 2. Agent de Diagnostic AMR (Autonomous Mobile Robots)
- **Rôle** : Spécialisé dans l'analyse de la connectivité pour robots mobiles
- **Fonctionnalités** :
  - Monitoring des handovers entre points d'accès
  - Analyse des interruptions de connexion
  - Évaluation de la stabilité pour applications critiques
  - Recommandations d'optimisation réseau

### 3. Agent de Génération de Rapports
- **Rôle** : Création automatique de rapports d'analyse
- **Fonctionnalités** :
  - Formatage conversationnel des données techniques
  - Génération de recommandations IT
  - Création de résumés exécutifs
  - Export multi-format (TXT, JSON, HTML)

### 4. Agent de Détection d'Anomalies
- **Rôle** : Identification proactive des problèmes réseau
- **Fonctionnalités** :
  - Algorithmes de détection de seuils adaptatifs
  - Corrélation multi-métriques
  - Prédiction de dégradations
  - Classification automatique des incidents

## 🔧 Configuration des Agents

### Paramètres Globaux
```yaml
agents:
  update_interval: 1000  # ms
  alert_thresholds:
    signal_critical: -85   # dBm
    quality_critical: 20   # %
    latency_critical: 100  # ms

  analysis_window: 300     # échantillons pour calculs
  prediction_enabled: true
```

### Seuils d'Alerte Adaptatifs
Les agents utilisent des seuils dynamiques basés sur :
- Historique des performances
- Patterns temporels (jour/nuit)
- Type d'environnement (bureau, entrepôt, etc.)

## 📊 Intégration avec OpenAI

### Instructions Personnalisées
Les agents peuvent être configurés pour utiliser les instructions personnalisées OpenAI :

```markdown
Vous êtes un expert en réseaux WiFi industriels spécialisé dans :
- L'analyse de performance pour robots mobiles autonomes (AMR)
- Le diagnostic des problèmes de connectivité
- L'optimisation des infrastructures sans fil
- La génération de rapports techniques

Analysez les données en français et fournissez des recommandations concrètes.
```

### Utilisation avec l'API OpenAI
- **Endpoint** : `/v1/chat/completions`
- **Modèle recommandé** : `gpt-4` ou `gpt-3.5-turbo`
- **Température** : `0.3` (pour des réponses techniques précises)

## 🚀 Agents Spécialisés

### Agent de Monitoring Moxa
- **Fichier** : `moxa_analyzer.py`
- **Fonction** : Analyse des logs et événements Moxa
- **Spécialités** :
  - Parsing des logs système
  - Détection des déconnexions
  - Analyse des patterns de roaming

### Agent de Gestion des BSSID
- **Fichier** : `mac_tag_manager.py`
- **Fonction** : Identification et étiquetage des points d'accès
- **Spécialités** :
  - Mapping automatique des adresses MAC
  - Gestion des tags personnalisés
  - Historique des associations

### Agent de Génération de Heatmaps
- **Fichier** : `heatmap_generator.py`
- **Fonction** : Visualisation spatiale de la couverture
- **Spécialités** :
  - Cartographie de la force du signal
  - Zones de couverture optimale
  - Identification des zones mortes

## 🎯 Cas d'Usage par Secteur

### Industrie 4.0 / Logistique
- **Focus** : AMR et véhicules autonomes
- **Métriques clés** : Handover, latence, stabilité
- **Seuils** : Très stricts pour continuité opérationnelle

### Bureaux / Entreprises
- **Focus** : Productivité utilisateurs
- **Métriques clés** : Débit, qualité, couverture
- **Seuils** : Standards pour applications business

### Retail / Commerce
- **Focus** : Expérience client et IoT
- **Métriques clés** : Disponibilité, capacité
- **Seuils** : Équilibrés performance/coût

## 🔍 Fonctionnalités Avancées

### Intelligence Prédictive
```python
def predict_degradation(self, samples):
    """Prédit les dégradations futures basées sur les tendances"""
    # Algorithme de machine learning pour prédiction
    # Analyse des patterns historiques
    # Génération d'alertes préventives
```

### Auto-optimisation
```python
def optimize_thresholds(self, environment_type):
    """Ajuste automatiquement les seuils selon l'environnement"""
    # Adaptation aux conditions locales
    # Apprentissage des patterns normaux
    # Réduction des faux positifs
```

### Corrélation Multi-Sources
```python
def correlate_events(self, wifi_data, moxa_logs, infrastructure_data):
    """Corrèle les événements de différentes sources"""
    # Analyse cross-platform
    # Identification des causes racines
    # Génération de diagnostics complets
```

## 📈 Métriques de Performance des Agents

### Indicateurs Clés
- **Précision de détection** : > 95%
- **Temps de réponse** : < 2 secondes
- **Faux positifs** : < 5%
- **Couverture d'analyse** : 100% des échantillons

### Monitoring des Agents
```python
agent_metrics = {
    "uptime": "99.9%",
    "processing_rate": "1000 samples/sec",
    "memory_usage": "< 100MB",
    "cpu_utilization": "< 10%"
}
```

## 🛠 Développement et Extension

### Ajouter un Nouvel Agent
1. Hériter de la classe `BaseAgent`
2. Implémenter les méthodes requises
3. Configurer les paramètres spécifiques
4. Intégrer dans le pipeline principal

### Exemple de Structure
```python
class CustomWifiAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        self.specialized_params = config.get('custom_params', {})

    def process_sample(self, sample):
        # Logique spécialisée
        pass

    def generate_insights(self, data):
        # Génération d'insights personnalisés
        pass
```

## 📝 Logs et Debugging

### Niveaux de Log
- **DEBUG** : Détails techniques complets
- **INFO** : Événements normaux d'opération
- **WARNING** : Situations nécessitant attention
- **ERROR** : Erreurs critiques nécessitant intervention

### Fichiers de Log
- `network_analysis.log` : Log principal de l'application
- `wifi_analyzer.log` : Log spécifique aux analyses WiFi
- `api_errors.log` : Erreurs d'intégration API

## 🔗 Intégrations Externes

### APIs Supportées
- **OpenAI GPT** : Génération de rapports intelligents
- **Microsoft Graph** : Intégration Office 365
- **Slack/Teams** : Notifications automatiques
- **SNMP** : Monitoring équipements réseau

### Webhooks
Configuration de notifications en temps réel vers systèmes externes.

---

## 📞 Support et Contact

Pour questions techniques ou suggestions d'améliorations :
- **Email** : support@noovelia.com
- **Documentation** : Voir `README.md` et guides spécialisés
- **Issues** : Utiliser le système de tickets du projet

---

*Document mis à jour le : 29 Mai 2025*
*Version de l'application : 2.0*
