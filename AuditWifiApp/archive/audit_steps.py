# -*- coding: utf-8 -*-
import os
import time
import json
from datetime import datetime
import winsound  # Pour les notifications sonores
from moxa_analyzer import MoxaLogAnalyzer
from moxa_config_analyzer import MoxaConfigAnalyzer

class AuditStep:
    def __init__(self, name, description, criteria):
        self.name = name
        self.description = description
        self.criteria = criteria
        self.completed = False
        self.start_time = None
        self.end_time = None
        self.data = {}
        
    def start(self):
        self.start_time = datetime.now()
        
    def complete(self, success=True, data=None):
        self.completed = success
        self.end_time = datetime.now()
        if data:
            self.data.update(data)

class MoxaAuditStep(AuditStep):
    """Étape d'audit spécifique pour l'analyse Moxa avec gestion des configurations et logs"""
    def __init__(self):
        super().__init__(
            "Analyse Moxa",
            "Analyser les logs Moxa et suggérer des améliorations",
            {"min_score": 70}  # Score minimum pour passer
        )
        self.analyzer = MoxaLogAnalyzer()
        self.config_params = {
            'min_transmission_rate': None,
            'max_transmission_power': None,
            'rts_threshold': None,
            'fragmentation_threshold': None,
            'roaming_mechanism': None,
            'roaming_difference': None, 
            'remote_connection_check': None,
            'wmm_enabled': None,
            'turbo_roaming': None,
            'ap_alive_check': None
        }
        self.log_content = ""
        self.analysis_results = None
        self.settings_provided = False
        self.log_provided = False
        
    def set_config_params(self, config_dict):
        """Définir les paramètres de configuration Moxa"""
        for key, value in config_dict.items():
            if key in self.config_params:
                self.config_params[key] = value
        self.analyzer.set_current_config(self.config_params)
        self.settings_provided = True
        return True
        
    def set_log_content(self, log_text):
        """Définir le contenu du log Moxa à analyser"""
        self.log_content = log_text
        self.log_provided = True
        return True
    
    def parse_settings_text(self, settings_text):
        """Extraire les paramètres à partir du texte collé"""
        config = {}
        
        # Recherche des paramètres communs dans le texte
        import re
        
        # Min transmission rate
        min_rate_match = re.search(r'[Mm]in[imum]*\s*[Tt]ransmission\s*[Rr]ate\s*[=:]\s*(\d+)', settings_text)
        if min_rate_match:
            config['min_transmission_rate'] = int(min_rate_match.group(1))
        
        # Max transmission power
        max_power_match = re.search(r'[Mm]ax[imum]*\s*[Tt]ransmission\s*[Pp]ower\s*[=:]\s*(\d+)', settings_text)
        if max_power_match:
            config['max_transmission_power'] = int(max_power_match.group(1))
        
        # RTS threshold
        rts_match = re.search(r'[Rr][Tt][Ss]\s*[Tt]hreshold\s*[=:]\s*(\d+)', settings_text)
        if rts_match:
            config['rts_threshold'] = int(rts_match.group(1))
            
        # Fragmentation threshold
        frag_match = re.search(r'[Ff]ragmentation\s*[Tt]hreshold\s*[=:]\s*(\d+)', settings_text)
        if frag_match:
            config['fragmentation_threshold'] = int(frag_match.group(1))
        
        # Roaming mechanism
        if re.search(r'[Rr]oaming\s*(?:[Mm]echanism|[Tt]hreshold|[Mm]ode)\s*[=:]\s*(?:[Bb]ased\s*on)?\s*SNR', settings_text):
            config['roaming_mechanism'] = 'snr'
        elif re.search(r'[Rr]oaming\s*(?:[Mm]echanism|[Tt]hreshold|[Mm]ode)\s*[=:]\s*(?:[Bb]ased\s*on)?\s*[Ss]ignal\s*[Ss]trength', settings_text):
            config['roaming_mechanism'] = 'signal_strength'
        
        # Roaming difference
        roam_diff_match = re.search(r'[Rr]oaming\s*[Dd]ifference\s*[=:]\s*(\d+)', settings_text)
        if roam_diff_match:
            config['roaming_difference'] = int(roam_diff_match.group(1))
        
        # Remote connection check
        remote_check = re.search(r'[Rr]emote\s*[Cc]onnection\s*[Cc]heck\s*[=:]\s*([Ee]nable|[Dd]isable|[Oo]n|[Oo]ff|[Tt]rue|[Ff]alse|1|0)', settings_text)
        if remote_check:
            value = remote_check.group(1).lower()
            config['remote_connection_check'] = value in ['enable', 'on', 'true', '1']
            
        # WMM
        wmm_match = re.search(r'WMM\s*[=:]\s*([Ee]nable|[Dd]isable|[Oo]n|[Oo]ff|[Tt]rue|[Ff]alse|1|0)', settings_text)
        if wmm_match:
            value = wmm_match.group(1).lower()
            config['wmm_enabled'] = value in ['enable', 'on', 'true', '1']
            
        # Turbo Roaming
        turbo_match = re.search(r'[Tt]urbo\s*[Rr]oaming\s*[=:]\s*([Ee]nable|[Dd]isable|[Oo]n|[Oo]ff|[Tt]rue|[Ff]alse|1|0)', settings_text)
        if turbo_match:
            value = turbo_match.group(1).lower()
            config['turbo_roaming'] = value in ['enable', 'on', 'true', '1']
            
        # AP Alive Check
        ap_alive_match = re.search(r'AP\s*[Aa]live\s*[Cc]heck\s*[=:]\s*([Ee]nable|[Dd]isable|[Oo]n|[Oo]ff|[Tt]rue|[Ff]alse|1|0)', settings_text)
        if ap_alive_match:
            value = ap_alive_match.group(1).lower()
            config['ap_alive_check'] = value in ['enable', 'on', 'true', '1']
        
        return self.set_config_params(config)
    
    def analyze_log(self):
        """Analyser le log Moxa et générer des recommandations"""
        # Sauvegarder le log dans un fichier temporaire pour analyse
        temp_log_path = os.path.join("logs_moxa", f"moxa_log_{time.strftime('%Y-%m-%d')}.txt")
        os.makedirs(os.path.dirname(temp_log_path), exist_ok=True)
        
        with open(temp_log_path, 'w', encoding='utf-8') as f:
            f.write(self.log_content)
        
        # Analyser le log
        success = self.analyzer.parse_log_file(temp_log_path)
        if success:
            self.analyzer.evaluate_parameters()
            self.analysis_results = {
                'score': self.analyzer.results['score'],
                'recommendations': self.analyzer.results['recommendations'],
                'config_changes': self.analyzer.results['config_changes'],
                'details': self.analyzer.results['details']
            }
            
            # Sauvegarder les résultats pour référence
            results_path = os.path.join("logs_moxa", f"analysis_{time.strftime('%Y-%m-%d')}.json")
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
                
            return self.analysis_results
        else:
            return {'error': 'Impossible d\'analyser le log Moxa'}
    
    def get_parameter_status(self):
        """Récupère l'état des paramètres actuels et les recommandations"""
        if not self.analysis_results:
            return None
        
        status = {
            'score': self.analysis_results['score'],
            'parameters': [],
            'recommendations': self.analysis_results['recommendations']
        }
        
        # Formater les paramètres et leurs états
        for param_name, details in self.analysis_results.get('details', {}).items():
            param_info = {
                'name': param_name,
                'current_value': details.get('value', 'Non défini'),
                'ideal_value': details.get('ideal_value', 'Non défini'),
                'status': details.get('status', 'unknown'),
            }
            status['parameters'].append(param_info)
        
        return status
        
    def run_optimizer(self, root=None):
        """Lancer l'outil d'optimisation Moxa avec l'interface graphique intégrée
        
        Args:
            root: racine Tkinter à utiliser (None pour en créer une nouvelle)
            
        Returns:
            bool: True si l'optimiseur a bien été lancé, False sinon
        """
        try:
            import tkinter as tk
            
            # Si aucune racine n'est fournie, en créer une nouvelle
            if root is None:
                new_window = tk.Toplevel()
                new_window.title("Optimiseur Moxa")
                new_window.geometry("950x700")
                root = new_window
            
            # Création de l'analyseur de configuration
            optimizer = MoxaConfigAnalyzer(root)
            
            # Si nous avons déjà des paramètres, les définir dans l'optimiseur
            if self.settings_provided:
                for param, value in self.config_params.items():
                    if value is not None:
                        if param == 'min_transmission_rate':
                            optimizer.min_transmission_rate.set(str(value))
                        elif param == 'max_transmission_power':
                            optimizer.max_transmission_power.set(str(value))
                        elif param == 'rts_threshold':
                            optimizer.rts_threshold.set(str(value))
                        elif param == 'fragmentation_threshold':
                            optimizer.fragmentation_threshold.set(str(value))
                        elif param == 'roaming_mechanism':
                            optimizer.roaming_mechanism.set(value)
                        elif param == 'roaming_difference':
                            optimizer.roaming_difference.set(str(value))
                        elif param == 'remote_connection_check':
                            optimizer.remote_connection_check.set(value)
                        elif param == 'wmm_enabled':
                            optimizer.wmm_enabled.set(value)
                        elif param == 'turbo_roaming':
                            optimizer.turbo_roaming.set(value)
                        elif param == 'ap_alive_check':
                            optimizer.ap_alive_check.set(value)
            
            # Si nous avons déjà du contenu de log, le définir dans l'optimiseur
            if self.log_provided:
                optimizer.log_text.delete("1.0", tk.END)
                optimizer.log_text.insert(tk.END, self.log_content)
            
            # Callback pour capturer les résultats de l'analyse
            def on_optimizer_analysis(results):
                if results and not isinstance(results, dict) or ('error' not in results):
                    self.analysis_results = results
                    self.settings_provided = True
                    # Mise à jour des paramètres
                    for param, details in results.get('details', {}).items():
                        if 'ideal_value' in details:
                            self.config_params[param] = details['ideal_value']
            
            # Connecter le callback à l'optimiseur
            optimizer.on_analysis_complete = on_optimizer_analysis
            
            return True
        except Exception as e:
            print(f"Erreur lors du lancement de l'optimiseur: {e}")
            return False
    
    def optimize_from_existing_data(self):
        """Analyser et générer des recommandations à partir des données existantes
        sans ouvrir l'interface utilisateur complète
        
        Returns:
            dict: Résultats de l'analyse ou None en cas d'erreur
        """
        if not self.settings_provided:
            return {'error': 'Aucun paramètre Moxa fourni'}
        
        if not self.log_provided:
            return {'error': 'Aucun log Moxa fourni'}
        
        return self.analyze_log()

class AuditManager:
    def __init__(self):
        self.steps = [
            AuditStep(
                "Tour de l'usine",
                "Faire le tour complet de l'usine en enregistrant les points faibles",
                {"min_coverage_points": 10, "max_weak_spots": 3}
            ),
            MoxaAuditStep(),  # Utilisation de la classe spécialisée pour l'étape Moxa
            AuditStep(
                "Rapport final",
                "Générer le rapport d'audit complet",
                {"all_steps_passed": True}
            )
        ]
        self.current_step = 0
        self.audit_data = {}
        
    def start_step(self):
        """Démarre l'étape courante"""
        if 0 <= self.current_step < len(self.steps):
            self.steps[self.current_step].start()
            return True
        return False
    
    def complete_step(self, success=True, data=None):
        """Complète l'étape courante"""
        if 0 <= self.current_step < len(self.steps):
            self.steps[self.current_step].complete(success, data)
            if success:
                self.current_step += 1
            return True
        return False
    
    def get_current_step(self):
        """Retourne l'étape courante"""
        if 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
    
    def play_notification(self):
        """Joue un son de notification"""
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            pass  # Ignorer si le son ne peut pas être joué
    
    def generate_report(self):
        """Génère le rapport final d'audit"""
        report = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "SUCCESS" if all(step.completed for step in self.steps) else "FAILED",
            "steps": []
        }
        
        for step in self.steps:
            step_report = {
                "name": step.name,
                "completed": step.completed,
                "duration": str(step.end_time - step.start_time) if step.end_time else None,
                "data": step.data
            }
            report["steps"].append(step_report)
            
        # Sauvegarder le rapport
        report_path = os.path.join("logs", f"audit_report_{time.strftime('%Y-%m-%d')}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        return report