# -*- coding: utf-8 -*-
import os
import json
import requests
from datetime import datetime
import api_config

class MoxaAIAnalyzer:
    """Analyseur de logs Moxa utilisant l'IA pour générer des recommandations"""
    
    def __init__(self, api_key=None, model="gpt-4o"):
        """
        Initialise l'analyseur IA.
        
        Args:
            api_key (str): Clé API pour le service d'IA (OpenAI par défaut)
            model (str): Modèle d'IA à utiliser
        """
        # Récupérer la clé API depuis différentes sources par ordre de priorité:
        # 1. Paramètre direct
        # 2. Fichier de configuration
        # 3. Variables d'environnement
        # 4. Clé par défaut
        if api_key:
            self.api_key = api_key
            # Sauvegarder automatiquement la clé pour les utilisations futures
            api_config.save_api_key(api_key)
        else:
            # Essayer de charger depuis la config
            self.api_key = api_config.get_api_key()
            
            # Si pas dans la config, utiliser les variables d'environnement
            if not self.api_key:
                self.api_key = os.environ.get("OPENAI_API_KEY")
            
            # Clé API par défaut (uniquement pour l'application AuditWifiApp)
            if not self.api_key:
                # Utilisation d'une clé hashée basique pour éviter de la stocker en clair
                # Note: ceci n'est pas sécurisé pour un usage en production
                self.api_key = self._get_default_api_key()
        
        self.model = model
        self.api_base_url = "https://api.openai.com/v1/chat/completions"
        
        # Paramètres idéaux pour la configuration Moxa
        self.ideal_config = {
            'min_transmission_rate': 12,
            'max_transmission_power': 20,
            'rts_threshold': 512,
            'fragmentation_threshold': 2346,
            'roaming_mechanism': 'snr',
            'roaming_difference': 8,
            'remote_connection_check': True,
            'wmm_enabled': True,
            'turbo_roaming': True,
            'ap_alive_check': True,
            'roaming_threshold_type': 'snr',
            'roaming_threshold_value': 40,  # SNR en dB, ou -75 en dBm si type est 'signal_strength'
            'ap_candidate_threshold_type': 'snr',
            'ap_candidate_threshold_value': 25,  # SNR en dB, ou -75 en dBm si type est 'signal_strength'
        }
        
        # Résultats de l'analyse
        self.results = {
            'score': 0,
            'max_score': 100,
            'roaming_metrics': {},
            'details': {},
            'recommendations': [],
            'config_changes': [],
            'ai_insights': "",
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _get_default_api_key(self):
        """Récupère la clé API par défaut pour l'application"""
        # Cette implementation de base n'est pas sécurisée pour un usage en production
        return "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"
    
    def set_api_key(self, api_key):
        """Définit la clé API pour le service d'IA et la sauvegarde dans la configuration"""
        self.api_key = api_key
        # Sauvegarder pour les utilisations futures
        api_config.save_api_key(api_key)
    
    def analyze_log(self, log_content, current_config, output_file=None):
        """
        Analyse les logs Moxa avec l'IA et génère des recommandations.
        
        Args:
            log_content (str): Contenu du log Moxa
            current_config (dict): Configuration actuelle du Moxa
            output_file (str, optional): Chemin vers le fichier de sortie pour les résultats
            
        Returns:
            dict: Résultats de l'analyse
        """
        if not self.api_key:
            raise ValueError("Aucune clé API fournie. Utilisez set_api_key() ou définissez la variable d'environnement OPENAI_API_KEY.")
        
        print("Analyse du log avec l'IA en cours...")
        
        # Tronquer le log si trop volumineux
        max_log_length = 15000  # Limite pour éviter des coûts API trop élevés
        if len(log_content) > max_log_length:
            truncated_log = log_content[:max_log_length] + "\n[Log tronqué pour limiter la taille...]"
            print(f"Log tronqué de {len(log_content)} à {max_log_length} caractères pour l'analyse IA.")
        else:
            truncated_log = log_content
        
        # Créer le prompt pour l'IA
        prompt = self._create_analysis_prompt(truncated_log, current_config)
        
        # Appeler l'API IA
        ai_response = self._call_ai_api(prompt)
        
        if not ai_response:
            print("Erreur: Aucune réponse de l'API IA")
            return None
        
        # Traiter la réponse de l'IA
        self.results = self._process_ai_response(ai_response, current_config)
        
        # Sauvegarder les résultats si un fichier de sortie est spécifié
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"Résultats sauvegardés dans {output_file}")
        
        return self.results
    
    def _create_analysis_prompt(self, log_content, current_config):
        """
        Crée le prompt pour l'analyse IA.
        
        Args:
            log_content (str): Contenu du log
            current_config (dict): Configuration actuelle
            
        Returns:
            str: Prompt pour l'API IA
        """
        # Convertir la configuration actuelle en texte formaté
        config_text = json.dumps(current_config, indent=2)
        
        # Créer le prompt avec instructions spécifiques pour l'IA
        prompt = f"""En tant qu'expert en réseaux sans fil et particulièrement en configuration d'appareils Moxa, analysez le log suivant et la configuration actuelle pour fournir des recommandations d'optimisation du roaming.

## Configuration actuelle du Moxa:
```json
{config_text}
```

## Objectifs de l'analyse:
1. Identifier les événements de roaming dans le log
2. Analyser les performances de roaming (temps de basculement, amélioration du SNR, etc.)
3. Évaluer si les paramètres actuels sont optimaux
4. Suggérer des modifications pour améliorer les performances de roaming

## Log Moxa à analyser:
```
{log_content}
```

## Paramètres idéaux pour référence:
- Taux de transmission min: 12 Mbps (améliore la fiabilité des transmissions)
- Puissance max: 20 dBm (équilibre entre portée et interférences)
- Seuil RTS: 512 (idéal pour environnements industriels avec interférences)
- Seuil de fragmentation: 2346 (évite la fragmentation inutile)
- Mécanisme de roaming: SNR (plus fiable que la force du signal)
- Différence de roaming: 8 dB (bon équilibre pour éviter l'effet ping-pong)
- Seuil de roaming (SNR): 40 dB (idéal pour environnements industriels)
- Seuil de roaming (Signal Strength): -75 dBm (idéal pour environnements industriels) 
- Seuil candidat AP (SNR): 25 dB (permet une bonne sélection d'AP)
- Seuil candidat AP (Signal Strength): -75 dBm (permet une bonne sélection d'AP)
- Vérification de connexion distante: Activée (améliore la détection des déconnexions)
- WMM: Activé (améliore la QoS)
- Turbo Roaming: Activé (réduit le temps de basculement)
- AP alive check: Activé (améliore la fiabilité)

## Format de réponse demandé (JSON):
```json
{
  "roaming_metrics": {
    "total_events": 0,
    "avg_handoff_time": 0,
    "min_handoff_time": 0,
    "max_handoff_time": 0,
    "avg_snr_before": 0,
    "avg_snr_after": 0,
    "snr_improvement": 0
  },
  "score": 0,
  "recommendations": [
    "Description détaillée de la recommandation 1",
    "Description détaillée de la recommandation 2"
  ],
  "config_changes": [
    {
      "param": "Nom du paramètre",
      "current": "Valeur actuelle",
      "recommended": "Valeur recommandée",
      "reason": "Raison détaillée du changement"
    }
  ],
  "analysis": "Analyse détaillée des performances de roaming, expliquant les problèmes identifiés et comment les changements recommandés les résoudront"
}
```

Fournissez votre réponse uniquement au format JSON demandé, sans texte supplémentaire.
"""
        return prompt
    
    def _call_ai_api(self, prompt):
        """
        Appelle l'API IA avec le prompt.
        
        Args:
            prompt (str): Prompt pour l'IA
            
        Returns:
            str: Réponse de l'IA
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,  # Valeur basse pour des réponses plus cohérentes
            "max_tokens": 4000
        }
        
        try:
            response = requests.post(
                self.api_base_url,
                headers=headers,
                json=data,
                timeout=60  # 60 secondes de timeout
            )
            
            if response.status_code == 200:
                response_json = response.json()
                return response_json["choices"][0]["message"]["content"]
            else:
                print(f"Erreur API ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"Erreur lors de l'appel API: {str(e)}")
            return None
    
    def _process_ai_response(self, ai_response, current_config):
        """
        Traite la réponse de l'IA et génère le rapport final.
        
        Args:
            ai_response (str): Réponse de l'IA
            current_config (dict): Configuration actuelle
            
        Returns:
            dict: Résultats formatés
        """
        try:
            # Extraire le JSON de la réponse (peut contenir du texte supplémentaire)
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_response = ai_response[json_start:json_end]
                ai_results = json.loads(json_response)
            else:
                # Essayer de parser directement si aucun JSON n'est trouvé
                ai_results = json.loads(ai_response)
            
            # Structure de base pour les résultats
            results = {
                'score': 0,
                'max_score': 100,
                'roaming_metrics': {},
                'recommendations': [],
                'config_changes': [],
                'ai_insights': "",
                'current_config': current_config,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Extraction des scores
            if 'score' in ai_results:
                try:
                    results['score'] = int(ai_results.get('score', 0))
                except (ValueError, TypeError):
                    # Si le score n'est pas un nombre, on utilise 0
                    results['score'] = 0
            
            # Extraction des métriques de roaming avec valeurs par défaut
            roaming_metrics = ai_results.get('roaming_metrics', {})
            if roaming_metrics:
                default_metrics = {
                    'total_events': 0,
                    'avg_handoff_time': 0,
                    'min_handoff_time': 0,
                    'max_handoff_time': 0,
                    'avg_snr_before': 0,
                    'avg_snr_after': 0,
                    'snr_improvement': 0
                }
                
                # S'assurer que toutes les métriques existent
                for key, default_value in default_metrics.items():
                    if key not in roaming_metrics or roaming_metrics[key] is None:
                        roaming_metrics[key] = default_value
                    elif not isinstance(roaming_metrics[key], (int, float)):
                        try:
                            roaming_metrics[key] = float(roaming_metrics[key])
                        except:
                            roaming_metrics[key] = default_value
                
                results['roaming_metrics'] = roaming_metrics
            
            # Extraction des recommandations
            if 'recommendations' in ai_results and isinstance(ai_results['recommendations'], list):
                results['recommendations'] = ai_results['recommendations']
            
            # Extraction des changements de configuration
            if 'config_changes' in ai_results and isinstance(ai_results['config_changes'], list):
                results['config_changes'] = ai_results['config_changes']
            
            # Extraction des insights (analyse détaillée)
            if 'analysis' in ai_results:
                results['ai_insights'] = ai_results['analysis']
            
            # Calculer le statut global
            score_percent = (results['score'] / results['max_score']) * 100
            if score_percent >= 80:
                results['status'] = "EXCELLENT"
            elif score_percent >= 60:
                results['status'] = "PASSABLE"
            else:
                results['status'] = "INSUFFISANT"
            
            return results
            
        except Exception as e:
            print(f"Erreur lors du traitement de la réponse IA: {str(e)}")
            print(f"Réponse brute: {ai_response}")
            
            # Retourner un résultat minimal en cas d'échec
            return {
                'score': 0,
                'max_score': 100,
                'status': "ERREUR",
                'error_message': f"Impossible de traiter la réponse de l'IA: {str(e)}",
                'raw_response': ai_response,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_user_friendly_report(self):
        """
        Génère un rapport formaté en texte lisible.
        
        Returns:
            str: Rapport formaté
        """
        if not self.results or not self.results.get('score'):
            return "Aucune analyse disponible. Exécutez d'abord 'analyze_log()'."
        
        # Calcul du score en pourcentage
        score_percent = int((self.results['score'] / self.results['max_score']) * 100)
        status = self.results.get('status', "INCONNU")
        
        # Créer le rapport
        report = []
        report.append("=" * 60)
        report.append(f"RAPPORT D'ANALYSE MOXA IA - {self.results.get('timestamp', 'Date inconnue')}")
        report.append("=" * 60)
        
        report.append(f"\nSCORE GLOBAL: {score_percent}% - {status}")
        
        # Métriques de roaming
        metrics = self.results.get('roaming_metrics', {})
        if metrics:
            report.append("\n--- MÉTRIQUES DE ROAMING ---")
            report.append(f"Événements de roaming: {metrics.get('total_events', 0)}")
            report.append(f"Temps de basculement moyen: {metrics.get('avg_handoff_time', 0)} ms")
            report.append(f"Temps min/max: {metrics.get('min_handoff_time', 0)} / {metrics.get('max_handoff_time', 0)} ms")
            report.append(f"SNR moyen avant roaming: {metrics.get('avg_snr_before', 0)} dB")
            report.append(f"SNR moyen après roaming: {metrics.get('avg_snr_after', 0)} dB")
            report.append(f"Amélioration moyenne du SNR: {metrics.get('snr_improvement', 0)} dB")
        
        # Recommandations
        recommendations = self.results.get('recommendations', [])
        if recommendations:
            report.append("\n--- RECOMMANDATIONS ---")
            for i, rec in enumerate(recommendations, 1):
                report.append(f"{i}. {rec}")
        
        # Changements de configuration
        config_changes = self.results.get('config_changes', [])
        if config_changes:
            report.append("\n--- CHANGEMENTS DE CONFIGURATION RECOMMANDÉS ---")
            for i, change in enumerate(config_changes, 1):
                report.append(f"{i}. Modifier '{change.get('param', '')}':")
                report.append(f"   - De: {change.get('current', '')}")
                report.append(f"   - À:  {change.get('recommended', '')}")
                report.append(f"   - Raison: {change.get('reason', '')}")
        
        # Analyse détaillée
        insights = self.results.get('ai_insights', "")
        if insights:
            report.append("\n--- ANALYSE DÉTAILLÉE ---")
            report.append(insights)
        
        report.append("\n" + "=" * 60)
        report.append("Fin du rapport d'analyse IA")
        
        return "\n".join(report)
    
    def analyze_configuration(self, current_config):
        """
        Analyse la configuration actuelle du Moxa et récupère les logs pour générer des recommandations.
        
        Args:
            current_config (dict): Configuration actuelle du Moxa
            
        Returns:
            dict: Résultats de l'analyse avec recommandations
        """
        try:
            # Récupérer les logs récents
            logs_dir = "logs_moxa"
            os.makedirs(logs_dir, exist_ok=True)
            
            # Chercher le fichier log le plus récent
            log_files = [f for f in os.listdir(logs_dir) if f.startswith("moxa_log_") and f.endswith(".txt")]
            
            # Si aucun fichier log n'existe, créer un message d'erreur
            if not log_files:
                # Obtenir le texte du widget de log dans l'interface
                log_content = "Pas de fichier log trouvé. Utilisez le texte affiché dans l'interface."
                
                # Si le texte de l'interface est vide, utiliser les logs d'exemple
                if not log_content.strip():
                    log_content = """
                    [WLAN] Roaming from AP [MAC: B2:46:19D1:1D:D8:6A, SNR: 15, Noise Floor: -95] to AP [MAC: B2:46:19D1:1D:D8:74, SNR: 29, Noise Floor: -95].
                    [WLAN] Disconnected from AP [B2:46:19D1:1D:D8:6A]; last association: 696619 ms. id (0/4)
                    [WLAN] Successfully associated with AP [B2:46:19D1:1D:D8:74].
                    [WLAN] Successfully connected to AP [B2:46:19D1:1D:D8:74]; handoff time: 62 ms. index(2)
                    """
            else:
                # Utiliser le fichier log le plus récent
                latest_log = max(log_files)
                log_file_path = os.path.join(logs_dir, latest_log)
                
                try:
                    with open(log_file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                        log_content = f.read()
                except Exception as e:
                    return {
                        'score': 0,
                        'max_score': 100,
                        'status': "ERREUR",
                        'error_message': f"Erreur de lecture du fichier log: {str(e)}",
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
            
            # Analyser les logs avec l'IA
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(logs_dir, f"results_{timestamp}.json")
            
            results = self.analyze_log(log_content, current_config, output_file)
            return results
            
        except Exception as e:
            return {
                'score': 0,
                'max_score': 100,
                'status': "ERREUR",
                'error_message': f"Erreur lors de l'analyse de la configuration: {str(e)}",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }


# Fonction utilitaire pour tester rapidement
def analyze_moxa_log_with_ai(log_file, config, api_key=None, output_file=None):
    """
    Fonction utilitaire pour analyser rapidement un log Moxa avec l'IA.
    
    Args:
        log_file (str): Chemin vers le fichier log
        config (dict): Configuration Moxa actuelle
        api_key (str, optional): Clé API pour le service d'IA
        output_file (str, optional): Fichier de sortie pour les résultats
        
    Returns:
        dict: Résultats de l'analyse
    """
    try:
        with open(log_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
            log_content = f.read()
        
        analyzer = MoxaAIAnalyzer(api_key)
        results = analyzer.analyze_log(log_content, config, output_file)
        
        print(analyzer.get_user_friendly_report())
        return results
        
    except Exception as e:
        print(f"Erreur lors de l'analyse: {str(e)}")
        return None


# Code d'exemple pour utiliser le module
if __name__ == "__main__":
    # Configuration de test
    test_config = {
        'min_transmission_rate': 6,
        'max_transmission_power': 20,
        'rts_threshold': 512,
        'fragmentation_threshold': 2346,
        'roaming_mechanism': 'signal_strength',
        'roaming_difference': 9,
        'remote_connection_check': True,
        'wmm_enabled': True,
        'turbo_roaming': True,
        'ap_alive_check': True
    }
    
    # Demander la clé API si non définie dans les variables d'environnement
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Entrez votre clé API OpenAI: ").strip()
    
    # Demander le chemin du fichier log
    log_file = input("Entrez le chemin du fichier log Moxa (ou appuyez sur Entrée pour utiliser logs_moxa/temp_log.txt): ").strip()
    if not log_file:
        log_file = "logs_moxa/temp_log.txt"
    
    # Analyser le log
    if os.path.exists(log_file):
        results_file = f"logs_moxa/ai_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        analyze_moxa_log_with_ai(log_file, test_config, api_key, results_file)
    else:
        print(f"Erreur: Le fichier {log_file} n'existe pas.")