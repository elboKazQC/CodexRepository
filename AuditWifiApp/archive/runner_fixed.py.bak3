# -*- coding: utf-8 -*-
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from dotenv import load_dotenv
from datetime import datetime
import threading
import time
import logging
import subprocess
from wifi_data_collector import WifiDataCollector, WifiSample, SpeedTest, PingTest
from config_manager import ConfigurationManager
from log_manager import LogManager
from wifi_test_manager import WifiTestManager
from moxa_log_analyzer import MoxaLogAnalyzer
from moxa_roaming_analyzer import MoxaRoamingAnalyzer
from wifi_log_analyzer import WifiLogAnalyzer
from wifi_signal_analyzer import WifiAnalyzer
from wifi_coverage_analyzer import WifiCoverageAnalyzer

# Configuration de la journalisation
logging.basicConfig(
    filename="api_errors.log",
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Charger les variables d'environnement
load_dotenv()

class MoxaAnalyzerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyseur de Configuration Moxa")

        # Configuration par défaut
        self.max_log_length = 20000  # Augmentation de la limite de logs à 20 000 caractères
        default_config = {
            "min_transmission_rate": 6,
            "max_transmission_power": 20,
            "rts_threshold": 512,
            "fragmentation_threshold": 2346,
            "roaming_mechanism": "signal_strength",
            "roaming_difference": 9,
            "remote_connection_check": True,
            "wmm_enabled": True,
            "turbo_roaming": True,
            "ap_alive_check": True,
            "roaming_threshold_type": "signal_strength",
            "roaming_threshold_value": -70,
            "ap_candidate_threshold_type": "signal_strength",
            "ap_candidate_threshold_value": -70
        }

        # Utilisation de ConfigurationManager, LogManager et WifiTestManager
        self.config_manager = ConfigurationManager(default_config)
        self.log_manager = LogManager()
        self.wifi_test_manager = WifiTestManager(WifiDataCollector())
        self.setup_ui()

    def setup_ui(self):
        # Frame principal avec padding réduit
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame gauche (configuration)
        left_frame = ttk.Frame(main_frame)
        main_frame.add(left_frame, weight=1)
        
        # Frame droite (résultats)
        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=1)
        
        # Notebook pour organiser les sections de gauche
        left_notebook = ttk.Notebook(left_frame)
        left_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet Configuration
        config_tab = ttk.Frame(left_notebook)
        left_notebook.add(config_tab, text="Configuration")
        self.setup_config_section(config_tab)
        
        # Onglet Logs
        logs_tab = ttk.Frame(left_notebook)
        left_notebook.add(logs_tab, text="Logs")
        self.setup_logs_input_section(logs_tab)
        
        # Onglet Tests WiFi
        wifi_tab = ttk.Frame(left_notebook)
        left_notebook.add(wifi_tab, text="Tests WiFi")
        self.setup_wifi_test_section(wifi_tab)
        
        # Configuration de la section résultats
        self.setup_results_section(right_frame)

    def setup_config_section(self, parent):
        # Configuration Frame
        config_frame = ttk.LabelFrame(parent, text="Configuration Moxa", padding=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Ajouter les champs de configuration...
        self.add_config_fields(config_frame)

        # Ajouter les boutons Sauvegarder et Charger
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Sauvegarder", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Charger", command=self.load_config).pack(side=tk.LEFT, padx=5)

    def add_config_fields(self, frame):
        # Créer un canvas avec scrollbar pour les paramètres de configuration
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        config_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack les widgets
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Créer une fenêtre dans le canvas pour le frame
        canvas_window = canvas.create_window((0, 0), window=config_frame, anchor="nw")
        
        # Créer les champs pour chaque paramètre de configuration
        row = 0
        for key, value in self.config_manager.get_config().items():
            label = ttk.Label(config_frame, text=key.replace("_", " ").title())
            label.grid(row=row, column=0, sticky=tk.W, padx=2, pady=1)
            
            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                widget = ttk.Checkbutton(config_frame, variable=var)
            else:
                var = tk.StringVar(value=str(value))
                entry = ttk.Entry(config_frame, textvariable=var, width=15)
                widget = entry
            
            widget.grid(row=row, column=1, sticky=tk.W, padx=2, pady=1)
            setattr(self, f"var_{key}", var)
            row += 1
        
        # Configurer le scrolling
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        config_frame.bind("<Configure>", configure_scroll)
        canvas.bind("<Configure>", configure_canvas)
        
        # Permettre le scrolling avec la molette de la souris
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)

    def setup_logs_input_section(self, parent):
        """Configure la section pour coller et analyser les logs"""
        # Section pour coller les logs
        logs_input_frame = ttk.LabelFrame(parent, text="Coller les Logs", padding=10)
        logs_input_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Zone de texte pour coller les logs avec scrollbar
        text_frame = ttk.Frame(logs_input_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.logs_input_text = tk.Text(text_frame, wrap=tk.WORD, height=10)
        self.logs_input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.logs_input_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.logs_input_text.configure(yscrollcommand=scrollbar.set)

        # Boutons d'analyse
        analyze_button_frame = ttk.Frame(logs_input_frame)
        analyze_button_frame.pack(fill=tk.X, pady=5)

        # Bouton d'analyse
        analyze_btn = ttk.Button(analyze_button_frame, 
                          text="Analyser",
                          command=self.analyze_logs_from_input)
        analyze_btn.pack(side=tk.LEFT, padx=5)

        # Bouton pour charger depuis un fichier
        file_btn = ttk.Button(analyze_button_frame, 
                           text="Charger depuis fichier",
                           command=self.analyze_logs_from_file)
        file_btn.pack(side=tk.RIGHT, padx=5)

    def analyze_logs_from_input(self, log_content=None):
        """Analyse les logs fournis dans la zone de texte ou en paramètre."""
        if log_content is None:
            # Récupérer le contenu collé dans la zone de texte
            log_content = self.logs_input_text.get("1.0", tk.END).strip()

        if not log_content:
            messagebox.showerror("Erreur", "Veuillez fournir des logs à analyser.")
            return

        try:
            # Déterminer si c'est un log Moxa
            is_moxa_log = self.is_moxa_log(log_content)
            
            # Utiliser LogManager pour l'analyse
            results = self.log_manager.analyze_logs(
                log_content,
                self.config_manager.get_config(),
                is_moxa_log
            )

            # Vider la zone de résultats
            self.results_text.delete(1.0, tk.END)
            
            # Toujours utiliser le format conversationnel s'il est disponible
            if 'conversational' in results and results['conversational']:
                # Appliquer le formatage Markdown au texte conversationnel
                self.apply_markdown_formatting(results['conversational'])
            else:
                # Fallback au format traditionnel si le format conversationnel n'est pas disponible
                if is_moxa_log:
                    self.display_moxa_analysis(results)
                else:
                    self.display_wifi_analysis(results)

            # Activer le bouton de sauvegarde
            self.save_button.config(state=tk.NORMAL)

        except Exception as e:
            # Afficher l'erreur complète dans la zone de texte
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Erreur lors de l'analyse des logs:\n{str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de l'analyse des logs : {str(e)}")

    def display_results(self, results):
        self.results_text.delete(1.0, tk.END)

        # Titre principal
        self.results_text.insert(tk.END, "==== Résultats d'analyse ====\n\n")

        # Score
        score = results.get('score', 0) if isinstance(results, dict) else 0
        if score >= 80:
            self.results_text.insert(tk.END, f"Score : {score}/100 (SATISFAISANT)\nLa configuration actuelle est adéquate pour une performance Wi-Fi optimale.\n")
        else:
            self.results_text.insert(tk.END, f"Score : {score}/100\n")
        self.results_text.insert(tk.END, "\n")

        # Métriques de roaming (optionnel)
        self.results_text.insert(tk.END, "-- Métriques de roaming --\n")
        roaming_metrics = results.get('roaming_metrics', {}) if isinstance(results, dict) else {}
        if isinstance(roaming_metrics, dict) and roaming_metrics:
            for key, value in roaming_metrics.items():
                self.results_text.insert(tk.END, f"- {key.replace('_', ' ').capitalize()} : {value}\n")
        else:
            self.results_text.insert(tk.END, "Aucune métrique disponible.\n")
        self.results_text.insert(tk.END, "\n")

        # Recommandations (accepte 'recommandations' ou 'recommendations')
        self.results_text.insert(tk.END, "-- Recommandations personnalisées --\n")
        recommendations = results.get('recommandations') or results.get('recommendations') or []
        if isinstance(recommendations, dict):
            for k, v in recommendations.items():
                self.results_text.insert(tk.END, f"{k} : {v}\n")
            self.results_text.insert(tk.END, "\n")
        elif isinstance(recommendations, list) and recommendations:
            for i, rec in enumerate(recommendations):
                self.results_text.insert(tk.END, f"{i+1}. {rec}\n")
            self.results_text.insert(tk.END, "\n")
        elif isinstance(recommendations, str):
            self.results_text.insert(tk.END, recommendations + "\n\n")
        else:
            self.results_text.insert(tk.END, "Aucune recommandation disponible.\n\n")

        # APs problématiques (optionnel)
        self.results_text.insert(tk.END, "-- Points d'accès problématiques (SNR < 25) --\n")
        problematic_aps = results.get('problematic_aps', []) if isinstance(results, dict) else []
        ap_affiche = False
        if isinstance(problematic_aps, list) and problematic_aps:
            for ap in problematic_aps:
                if isinstance(ap, dict) and 'ap_mac' in ap:
                    ap_affiche = True
                    self.results_text.insert(tk.END, f"- {ap['ap_mac']} ({ap.get('occurrences', 'N/A')}x, SNR moyen : {ap.get('avg_snr', 'N/A')} dB)\n")
            if not ap_affiche:
                self.results_text.insert(tk.END, "Aucun point d'accès problématique détecté ou données incomplètes.\n")
        else:
            self.results_text.insert(tk.END, "Aucun point d'accès problématique détecté.\n")
        self.results_text.insert(tk.END, "\n")

        # Analyse détaillée (accepte 'analyse' ou 'analysis')
        self.results_text.insert(tk.END, "-- Analyse détaillée --\n")
        analysis = results.get('analyse') or results.get('analysis') or 'Aucune analyse disponible.'
        self.results_text.insert(tk.END, analysis + "\n")

        # Axes d'amélioration (accepte 'axes_amelioration' ou 'axes_d_amelioration')
        axes = results.get('axes_amelioration') or results.get('axes_d_amelioration')
        if axes:
            self.results_text.insert(tk.END, "\n-- Axes d'amélioration --\n")
            if isinstance(axes, list):
                for axe in axes:
                    self.results_text.insert(tk.END, f"- {axe}\n")
            elif isinstance(axes, str):
                self.results_text.insert(tk.END, axes + "\n")

    def display_moxa_analysis(self, analysis):
        """Affiche les résultats de l'analyse Moxa dans l'interface."""
        self.results_text.delete(1.0, tk.END)
        
        # Score global et adaptabilité
        self.results_text.insert(tk.END, "=== Analyse des Logs Moxa ===\n\n")
        self.results_text.insert(tk.END, f"Score global: {analysis.get('score_global', 'N/A')}/100\n")
        self.results_text.insert(tk.END, f"Adapté pour une flotte AMR: {'Oui' if analysis.get('adapte_flotte_AMR', False) else 'Non'}\n\n")

        # Analyse détaillée
        if 'analyse_detaillee' in analysis:
            details = analysis['analyse_detaillee']
            self.results_text.insert(tk.END, "=== Problèmes Détectés ===\n\n")

            # Effet ping-pong
            if 'ping_pong' in details:
                ping_pong = details['ping_pong']
                if ping_pong.get('detecte', False):
                    self.results_text.insert(tk.END, "1. Effet Ping-Pong:\n")
                    self.results_text.insert(tk.END, f"   • Gravité: {ping_pong.get('gravite', 'N/A')}/10\n")
                    if 'occurrences' in ping_pong:
                        self.results_text.insert(tk.END, "   • Occurrences:\n")
                        for occ in ping_pong['occurrences']:
                            self.results_text.insert(tk.END, f"     - {occ}\n")
                    self.results_text.insert(tk.END, "\n")

            # SNR problems
            if 'problemes_snr' in details:
                snr = details['problemes_snr']
                if snr.get('aps_snr_zero', []):
                    self.results_text.insert(tk.END, "2. Problèmes SNR:\n")
                    for ap in snr['aps_snr_zero']:
                        self.results_text.insert(tk.END, f"   • {ap}\n")
                    if 'details' in snr and 'episodes_critiques' in snr['details']:
                        self.results_text.insert(tk.END, "   • Épisodes critiques:\n")
                        for ep in snr['details']['episodes_critiques']:
                            self.results_text.insert(tk.END, f"     - AP {ep['ap']}: SNR {ep['snr']} à {ep['timestamp']}\n")
                    self.results_text.insert(tk.END, "\n")

            # Authentification
            if 'authentification' in details:
                auth = details['authentification']
                if auth.get('timeouts', 0) > 0 or auth.get('echecs', 0) > 0:
                    self.results_text.insert(tk.END, "3. Problèmes d'Authentification:\n")
                    self.results_text.insert(tk.END, f"   • Timeouts: {auth.get('timeouts', 'N/A')}\n")
                    self.results_text.insert(tk.END, f"   • Échecs: {auth.get('echecs', 'N/A')}\n")
                    if 'temps_moyen_ms' in auth:
                        self.results_text.insert(tk.END, f"   • Temps moyen: {auth['temps_moyen_ms']} ms\n")
                    self.results_text.insert(tk.END, "\n")

        # Recommandations
        if 'recommandations' in analysis and analysis['recommandations']:
            self.results_text.insert(tk.END, "=== Recommandations ===\n\n")
            for i, rec in enumerate(analysis['recommandations'], 1):
                self.results_text.insert(tk.END, f"{i}. {rec.get('probleme', 'N/A')}\n")
                self.results_text.insert(tk.END, f"   • Solution: {rec.get('solution', 'N/A')}\n")
                if 'parametres' in rec:
                    self.results_text.insert(tk.END, "   • Paramètres à modifier:\n")
                    for param, val in rec['parametres'].items():
                        self.results_text.insert(tk.END, f"     - {param}: {val}\n")
                self.results_text.insert(tk.END, "\n")

    def display_wifi_analysis(self, analysis):
        """Affiche les résultats de l'analyse WiFi dans l'interface."""
        self.results_text.delete(1.0, tk.END)
        
        # Score global et adaptabilité
        self.results_text.insert(tk.END, "=== Analyse des Logs WiFi ===\n\n")
        
        score = analysis.get('score_global', analysis.get('score', 0))
        self.results_text.insert(tk.END, f"Score global: {score}/100\n")
        
        adapte = analysis.get('adapte_flotte_AMR', analysis.get('adapte_pour_amr', False))
        self.results_text.insert(tk.END, f"Adapté pour une flotte AMR: {'Oui' if adapte else 'Non'}\n\n")

        # Métriques signal
        if 'analyse_detaillee' in analysis and 'signal' in analysis['analyse_detaillee']:
            signal = analysis['analyse_detaillee']['signal']
            self.results_text.insert(tk.END, "=== Qualité du Signal ===\n\n")
            self.results_text.insert(tk.END, f"• Niveau moyen: {signal.get('niveau_moyen', 'N/A')}\n")
            self.results_text.insert(tk.END, f"• Stabilité: {signal.get('stabilite', 'N/A')}/10\n")
            
            if 'zones_faibles' in signal and signal['zones_faibles']:
                self.results_text.insert(tk.END, "• Zones faibles:\n")
                for zone in signal['zones_faibles']:
                    self.results_text.insert(tk.END, f"  - {zone}\n")
            self.results_text.insert(tk.END, "\n")

        # Problèmes de connexion
        if 'analyse_detaillee' in analysis and 'connexion' in analysis['analyse_detaillee']:
            conn = analysis['analyse_detaillee']['connexion']
            self.results_text.insert(tk.END, "=== Problèmes de Connexion ===\n\n")
            self.results_text.insert(tk.END, f"• Déconnexions: {conn.get('deconnexions', 'N/A')}\n")
            self.results_text.insert(tk.END, f"• Échecs: {conn.get('echecs', 'N/A')}\n")
            self.results_text.insert(tk.END, f"• Temps moyen de connexion: {conn.get('temps_moyen_connexion', 'N/A')}\n")
            
            if 'details' in conn and 'causes_principales' in conn['details']:
                self.results_text.insert(tk.END, "• Causes principales:\n")
                for cause in conn['details']['causes_principales']:
                    self.results_text.insert(tk.END, f"  - {cause}\n")
            self.results_text.insert(tk.END, "\n")

        # Performance
        if 'analyse_detaillee' in analysis and 'performance' in analysis['analyse_detaillee']:
            perf = analysis['analyse_detaillee']['performance']
            self.results_text.insert(tk.END, "=== Performance ===\n\n")
            self.results_text.insert(tk.END, f"• Latence moyenne: {perf.get('latence_moyenne', 'N/A')}\n")
            self.results_text.insert(tk.END, f"• Débit moyen: {perf.get('debit_moyen', 'N/A')}\n")
            self.results_text.insert(tk.END, f"• Perte de paquets: {perf.get('perte_paquets', 'N/A')}\n\n")

        # Interférences
        if 'analyse_detaillee' in analysis and 'interferences' in analysis['analyse_detaillee']:
            interf = analysis['analyse_detaillee']['interferences']
            if interf.get('detectees', False):
                self.results_text.insert(tk.END, "=== Interférences ===\n\n")
                self.results_text.insert(tk.END, f"• Impact: {interf.get('impact', 'N/A')}/10\n")
                
                if 'sources_probables' in interf and interf['sources_probables']:
                    self.results_text.insert(tk.END, "• Sources probables:\n")
                    for source in interf['sources_probables']:
                        self.results_text.insert(tk.END, f"  - {source}\n")
                
                if 'details' in interf and 'canaux_affectes' in interf['details']:
                    self.results_text.insert(tk.END, "• Canaux affectés: ")
                    self.results_text.insert(tk.END, ", ".join(str(c) for c in interf['details']['canaux_affectes']))
                    self.results_text.insert(tk.END, "\n")
                self.results_text.insert(tk.END, "\n")

        # Recommandations
        if 'recommandations' in analysis and analysis['recommandations']:
            self.results_text.insert(tk.END, "=== Recommandations ===\n\n")
            
            for i, rec in enumerate(analysis['recommandations'], 1):
                if isinstance(rec, dict):
                    self.results_text.insert(tk.END, f"{i}. {rec.get('probleme', 'Problème non spécifié')}\n")
                    self.results_text.insert(tk.END, f"   • Solution: {rec.get('solution', 'N/A')}\n")
                    
                    if 'priorite' in rec:
                        self.results_text.insert(tk.END, f"   • Priorité: {rec.get('priorite', 'N/A')}/5\n")
                    
                    if 'parametres' in rec and rec['parametres']:
                        self.results_text.insert(tk.END, "   • Paramètres à modifier:\n")
                        for param, val in rec['parametres'].items():
                            self.results_text.insert(tk.END, f"     - {param}: {val}\n")
                else:
                    self.results_text.insert(tk.END, f"{i}. {rec}\n")
                
                self.results_text.insert(tk.END, "\n")

    def save_results(self, results):
        """Sauvegarde les résultats d'analyse dans un fichier JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs_moxa/results_{timestamp}.json"
        
        # Créer le dossier logs_moxa si nécessaire
        os.makedirs("logs_moxa", exist_ok=True)
        
        # Sauvegarder les résultats
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        messagebox.showinfo("Succès", f"Résultats sauvegardés dans {filename}")

    def setup_wifi_test_section(self, parent):
        """Configure la section pour les tests Wi-Fi"""
        wifi_test_frame = ttk.LabelFrame(parent, text="Tests Wi-Fi", padding=10)
        wifi_test_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame pour les contrôles
        controls_frame = ttk.Frame(wifi_test_frame)
        controls_frame.pack(fill=tk.X, pady=2)

        # Zone de test
        zone_frame = ttk.Frame(controls_frame)
        zone_frame.pack(fill=tk.X, pady=2)
        ttk.Label(zone_frame, text="Zone de test:").pack(side=tk.LEFT, padx=5)
        self.zone_var = tk.StringVar(value="Non spécifiée")
        zone_entry = ttk.Entry(zone_frame, textvariable=self.zone_var)
        zone_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        def update_zone(*args):
            self.current_zone = self.zone_var.get()
            if hasattr(self, 'wifi_test_manager'):
                self.wifi_test_manager.set_zone(self.current_zone)

        self.zone_var.trace_add("write", update_zone)

        # Boutons pour démarrer et arrêter les tests
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill=tk.X, pady=2)
        
        self.start_wifi_test_button = ttk.Button(buttons_frame, text="Démarrer le test Wi-Fi", command=self.start_wifi_test)
        self.start_wifi_test_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.stop_wifi_test_button = ttk.Button(buttons_frame, text="Arrêter le test Wi-Fi", command=self.stop_wifi_test, state=tk.DISABLED)
        self.stop_wifi_test_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Zone de texte pour afficher les résultats des tests Wi-Fi
        results_frame = ttk.Frame(wifi_test_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.wifi_test_results_text = tk.Text(results_frame, wrap=tk.WORD, height=10)
        self.wifi_test_results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar pour la zone de texte
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.wifi_test_results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.wifi_test_results_text.configure(yscrollcommand=scrollbar.set)

    def setup_results_section(self, parent):
        results_frame = ttk.Frame(parent)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Frame pour le titre des résultats
        title_frame = ttk.Frame(results_frame)
        title_frame.pack(fill=tk.X, padx=2, pady=1)
        ttk.Label(title_frame, text="Résultats d'analyse", font=("TkDefaultFont", 10, "bold")).pack(side=tk.LEFT)

        # Boutons d'actions sur les résultats
        actions_frame = ttk.Frame(title_frame)
        actions_frame.pack(side=tk.RIGHT)
        
        # Bouton pour sauvegarder les résultats
        self.save_button = ttk.Button(actions_frame, text="Sauvegarder", command=self.save_current_results)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        
        # Zone de texte pour les résultats avec scrollbar
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar pour les résultats
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Zone de texte pour les résultats, avec support du format markdown
        self.results_text = tk.Text(text_frame, wrap=tk.WORD, height=20, yscrollcommand=scrollbar.set)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=1)
        
        # Configuration des balises pour améliorer la présentation
        self.results_text.tag_configure("title", font=("TkDefaultFont", 12, "bold"))
        self.results_text.tag_configure("subtitle", font=("TkDefaultFont", 10, "bold"))
        self.results_text.tag_configure("normal", font=("TkDefaultFont", 9))
        self.results_text.tag_configure("bold", font=("TkDefaultFont", 9, "bold"))
        self.results_text.tag_configure("italic", font=("TkDefaultFont", 9, "italic"))
        
        # Configuration du scrollbar
        scrollbar.config(command=self.results_text.yview)
        
    def save_current_results(self):
        """Sauvegarde les résultats actuellement affichés au format texte"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Texte", "*.txt"), ("JSON", "*.json"), ("Tous les fichiers", "*.*")],
            initialfile=f"analyse_wifi_{timestamp}",
            title="Sauvegarder les résultats d'analyse"
        )
        
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                # Récupération du contenu affiché
                content = self.results_text.get("1.0", tk.END)
                f.write(content)
            
            messagebox.showinfo("Succès", f"Résultats sauvegardés dans {filename}")
        
    def apply_markdown_formatting(self, text):
        """
        Applique un formatage basique de type markdown au texte des résultats
        """
        self.results_text.delete(1.0, tk.END)
        
        lines = text.split('\n')
        for line in lines:
            # Titres
            if line.startswith('# '):
                self.results_text.insert(tk.END, line[2:] + "\n", "title")
            elif line.startswith('## '):
                self.results_text.insert(tk.END, line[3:] + "\n", "subtitle")
            elif line.startswith('### '):
                self.results_text.insert(tk.END, line[4:] + "\n", "subtitle")
            # Lignes de séparation
            elif line.startswith('---'):
                self.results_text.insert(tk.END, "─" * 50 + "\n", "normal")
            # Texte en gras avec emoji
            elif '**' in line:
                # Conserver les emojis avant le formatage
                emoji_parts = line.split(' ', 1)
                emoji = ""
                content = line
                
                if len(emoji_parts) > 1 and any(c in emoji_parts[0] for c in "📊📝🔌📡⚠️✅ℹ️🛠️🔍"):
                    emoji = emoji_parts[0] + " "
                    content = emoji_parts[1]
                
                if emoji:
                    self.results_text.insert(tk.END, emoji, "normal")
                
                # Traiter le contenu avec formatage gras
                parts = content.split('**')
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Partie entre **
                        self.results_text.insert(tk.END, part, "bold")
                    else:
                        self.results_text.insert(tk.END, part, "normal")
                self.results_text.insert(tk.END, "\n")
            # Texte en italique
            elif '*' in line and not line.startswith('---'):
                parts = line.split('*')
                for i, part in enumerate(parts):
                    if i % 2 == 1 and part:  # Partie entre * non vide
                        self.results_text.insert(tk.END, part, "italic")
                    else:
                        self.results_text.insert(tk.END, part, "normal")
                self.results_text.insert(tk.END, "\n")
            # Ligne normale avec émojis conservés
            else:
                self.results_text.insert(tk.END, line + "\n", "normal")

    def setup_action_buttons(self):
        # Suppression du bouton inutile avec des onglets
        pass
        
    def is_moxa_log(self, log_content):
        """
        Détermine si le contenu est un log Moxa en cherchant des patterns caractéristiques.
        """
        moxa_indicators = [
            "[WLAN] Roaming from AP",
            "Authentication request",
            "Deauthentication from AP",
            "SNR:",
            "Noise floor:",
            "[WLAN] Join ",
            "TransferRingToThread",            "AUTH-RECEIVE",
            "ASSOC-STATE",
            "WLAN-RECEIVE"
        ]
        
        return any(indicator in log_content for indicator in moxa_indicators)
        
    def analyze_wifi_with_ai(self):
        """Analyse les résultats des tests Wi-Fi avec une IA et affiche un score structuré."""
        wifi_logs = self.wifi_test_results_text.get("1.0", tk.END).strip()

        if not wifi_logs:
            messagebox.showerror("Erreur", "Aucun log Wi-Fi à analyser.")
            return

        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                messagebox.showerror("Erreur", "Clé API OpenAI non configurée.")
                return
            
            # Déterminer si c'est un log Moxa
            is_moxa_log = self.is_moxa_log(wifi_logs)
            
            # Utiliser LogManager pour l'analyse (il détectera automatiquement le type)
            results = self.log_manager.analyze_logs(
                wifi_logs,
                self.config_manager.get_config(),
                is_moxa_log
            )
            
            # Vider la zone de résultats
            self.results_text.delete(1.0, tk.END)
            
            if 'conversational' in results and results['conversational']:
                # Appliquer le formatage Markdown au texte conversationnel
                self.apply_markdown_formatting(results['conversational'])
            else:
                # Si aucun format conversationnel n'est disponible, utiliser l'affichage formaté habituel
                if is_moxa_log:
                    self.display_moxa_analysis(results)
                else:
                    self.display_wifi_analysis(results)
            
            # Activer le bouton de sauvegarde
            self.save_button.config(state=tk.NORMAL)
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'analyse: {str(e)}")

    def analyze_logs_from_file(self):
        """Permet de charger un fichier de logs et de lancer l'analyse."""
        filename = filedialog.askopenfilename(
            title="Sélectionner un fichier de logs",
            filetypes=[("Fichiers texte", "*.txt *.log"), ("Tous les fichiers", "*.*")],
            initialdir="logs_moxa"
        )
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    log_content = f.read()
                self.analyze_logs_from_input(log_content=log_content)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la lecture du fichier : {str(e)}")

    def save_config(self):
        """Sauvegarde la configuration actuelle."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            self.config_manager.save_config(filepath)

    def load_config(self):
        """Charge une configuration à partir d'un fichier."""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )        if filepath:
            self.config_manager.load_config(filepath)
            
    def get_current_config(self):
        """Retourne la configuration actuelle."""
        return self.config_manager.get_config()
        
    def start_wifi_test(self):
        """Démarre le test Wi-Fi."""
        # Initialiser la liste pour stocker toutes les données Wi-Fi collectées
        self.collected_wifi_data = []
        self.wifi_test_manager.start_wifi_test(self.update_wifi_test_results)
        self.start_wifi_test_button.config(state=tk.DISABLED)
        self.stop_wifi_test_button.config(state=tk.NORMAL)
        self.wifi_test_results_text.delete(1.0, tk.END)  # Effacer les résultats précédents
        self.wifi_test_results_text.insert(tk.END, "Test Wi-Fi démarré...\n")

    def stop_wifi_test(self):
        """Arrête le test Wi-Fi."""
        self.wifi_test_manager.stop_wifi_test()
        self.start_wifi_test_button.config(state=tk.NORMAL)
        self.stop_wifi_test_button.config(state=tk.DISABLED)
        self.wifi_test_results_text.insert(tk.END, "Test Wi-Fi arrêté. Analyse en cours...\n")
        # Analyse des données collectées
        self.analyze_wifi_test_logs()

    def update_wifi_test_results(self, result):
        """Met à jour l'interface utilisateur avec les résultats des tests Wi-Fi."""
        # Afficher le résultat dans l'interface
        timestamp = datetime.now().strftime("%H:%M:%S")
        info_line = f"[{timestamp}] {result}\n"
        self.wifi_test_results_text.insert(tk.END, info_line)
        self.wifi_test_results_text.see(tk.END)

        # Stocker les données pour analyse future
        network_data = {
            "timestamp": timestamp,
            "scan_number": len(self.collected_wifi_data) + 1,
            "ssid": result.ssid if hasattr(result, 'ssid') else "Inconnu",
            "bssid": result.bssid if hasattr(result, 'bssid') else "Inconnu",
            "signal_dbm": result.signal_dbm if hasattr(result, 'signal_dbm') else -100,
            "signal_percent": result.signal_percent if hasattr(result, 'signal_percent') else 0,
            "channel": result.channel if hasattr(result, 'channel') else 0,
            "frequency": result.frequency if hasattr(result, 'frequency') else "Inconnu",
            "frequency_mhz": result.frequency_mhz if hasattr(result, 'frequency_mhz') else 0,
            "channel_stability": "stable"  # Par défaut
        }
        self.collected_wifi_data.append(network_data)
        
    def analyze_wifi_test_logs(self):
        """Analyse les logs du test Wi-Fi à partir des données collectées"""
        if not hasattr(self, 'collected_wifi_data') or not self.collected_wifi_data:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Aucune donnée Wi-Fi collectée à analyser.\n")
            return

        # Stocker les BSSID uniques (points d'accès)
        unique_bssids = set()
        # Stocker les canaux utilisés
        channels_used = {}  # {channel: [bssids]}
        # Stocker tous les signaux pour calculer la moyenne
        all_signals = []
        # Stocker les BSSID avec signaux faibles
        weak_signal_bssids = set()
        # Suivre les changements de BSSID (roaming events)
        bssid_changes = []
        # BSSID précédent pour détecter les changements
        prev_strongest_bssid = None
        # Suivi des canaux variables par BSSID
        variable_channels = {}
        
        # Organiser les données par scan
        scans_data = {}
        for entry in self.collected_wifi_data:
            scan_num = entry["scan_number"]
            if scan_num not in scans_data:
                scans_data[scan_num] = []
            scans_data[scan_num].append(entry)
        
        # Analyser les données scan par scan
        for scan_num, scan_entries in sorted(scans_data.items()):
            # Trouver le point d'accès le plus fort dans ce scan
            strongest_entry = None
            for entry in scan_entries:
                # Collecter les statistiques
                signal_dbm = entry["signal_dbm"]
                bssid = entry["bssid"]
                channel = entry["channel"]
                
                unique_bssids.add(bssid)
                
                # Enregistrer le canal utilisé par ce BSSID
                if channel not in channels_used:
                    channels_used[channel] = []
                if bssid not in channels_used[channel]:
                    channels_used[channel].append(bssid)
                
                # Enregistrer le signal
                all_signals.append(signal_dbm)
                
                # Détecter les signaux faibles (< -70 dBm)
                if signal_dbm < -70:
                    weak_signal_bssids.add(bssid)
                
                # Vérifier si le canal change pour ce BSSID
                if "channel_stability" in entry and entry["channel_stability"] == "variable":
                    if bssid not in variable_channels:
                        variable_channels[bssid] = set()
                    variable_channels[bssid].add(channel)
                
                # Trouver l'entrée avec le signal le plus fort
                if strongest_entry is None or signal_dbm > strongest_entry["signal_dbm"]:
                    strongest_entry = entry
            
            # Détecter un événement de roaming (changement de BSSID le plus fort)
            if strongest_entry and prev_strongest_bssid and strongest_entry["bssid"] != prev_strongest_bssid:
                bssid_changes.append((prev_strongest_bssid, strongest_entry["bssid"], scan_num))
            
            # Mettre à jour le BSSID précédent
            if strongest_entry:
                prev_strongest_bssid = strongest_entry["bssid"]

        # Calculer les métriques
        signal_average = sum(all_signals) / len(all_signals) if all_signals else 0
        roaming_events = len(bssid_changes)
        weak_signal_zones = len(weak_signal_bssids)
        
        # Déterminer le niveau d'interférence en fonction du nombre de points d'accès sur les mêmes canaux
        # 2.4 GHz: canaux 1, 6, 11 sont non-chevauchants
        # 5 GHz: tous les canaux sont généralement non-chevauchants
        interference_channels = []
        for channel, bssids in channels_used.items():
            if len(bssids) > 1:
                interference_channels.append((channel, len(bssids)))
        
        # Calculer le score d'interférence
        interference_score = 0
        for channel, num_bssids in interference_channels:
            if channel in [1, 6, 11]:  # Canaux non-chevauchants en 2.4 GHz
                if num_bssids > 1:
                    interference_score += 1  # Interférence co-canal
            elif 1 <= channel <= 13:  # Canaux chevauchants en 2.4 GHz
                interference_score += 2  # Interférence due aux canaux adjacents
        
        if interference_score >= 5:
            interference_level = "Élevés"
        elif interference_score >= 2:
            interference_level = "Modérés"
        else:
            interference_level = "Faibles"

        # Calculer un score global sur 100
        score = 100
        
        # Pénalité pour signal faible
        if signal_average < -70:
            score -= 25
            signal_quality = "Mauvais"
        elif signal_average < -65:
            score -= 15
            signal_quality = "Moyen"
        elif signal_average < -60:
            score -= 5
            signal_quality = "Bon"
        else:
            signal_quality = "Excellent"
        
        # Pénalité pour roaming excessif
        if roaming_events > 5:
            score -= 20
            roaming_quality = "Mauvais"
        elif roaming_events > 2:
            score -= 10
            roaming_quality = "Moyen"
        else:
            roaming_quality = "Bon"
        
        # Pénalité pour zones à faible signal
        if weak_signal_zones > 3:
            score -= 20
        elif weak_signal_zones > 1:
            score -= 10
        
        # Pénalité pour interférences
        if interference_level == "Élevés":
            score -= 20
            interference_quality = "Mauvais"
        elif interference_level == "Modérés":
            score -= 10
            interference_quality = "Moyen"
        else:
            interference_quality = "Bon"
            
        # Pénalité pour canaux variables
        if len(variable_channels) > 1:
            score -= 15
            stability_quality = "Mauvais"
        elif len(variable_channels) == 1:
            score -= 5
            stability_quality = "Moyen"
        else:
            stability_quality = "Bon"
            
        # Limiter le score entre 0 et 100
        score = max(0, min(100, score))

        # Déterminer la qualité globale
        if score >= 90:
            quality_text = "Excellente"
        elif score >= 75:
            quality_text = "Bonne"
        elif score >= 60:
            quality_text = "Moyenne"
        elif score >= 40:
            quality_text = "Médiocre"
        else:
            quality_text = "Mauvaise"

        # Afficher les résultats dans la section principale
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Résultats des tests Wi-Fi:\n")
        self.results_text.insert(tk.END, f"Score global : {score}/100 (Qualité {quality_text})\n\n")
        
        self.results_text.insert(tk.END, "Détails de l'analyse:\n")
        self.results_text.insert(tk.END, f"- Points d'accès détectés : {len(unique_bssids)}\n")
        self.results_text.insert(tk.END, f"- Signal moyen : {signal_average:.1f} dBm ({signal_quality})\n")
        
        # Afficher les canaux utilisés avec le nombre de points d'accès
        self.results_text.insert(tk.END, "- Canaux utilisés :\n")
        for channel, bssids in sorted(channels_used.items()):
            self.results_text.insert(tk.END, f"  • Canal {channel}: {len(bssids)} point(s) d'accès\n")
        
        self.results_text.insert(tk.END, f"- Zones à faible signal détectées : {weak_signal_zones}\n")
        self.results_text.insert(tk.END, f"- Événements de roaming : {roaming_events} ({roaming_quality})\n")
        self.results_text.insert(tk.END, f"- Niveaux d'interférences : {interference_level} ({interference_quality})\n")
        
        if variable_channels:
            self.results_text.insert(tk.END, f"- Points d'accès avec canaux variables : {len(variable_channels)} ({stability_quality})\n")
            for bssid, channels in variable_channels.items():
                self.results_text.insert(tk.END, f"  • {bssid}: canaux {', '.join(map(str, sorted(channels)))}\n")
        
        self.results_text.insert(tk.END, "\n")

        # Afficher les événements de roaming
        if roaming_events > 0:
            self.results_text.insert(tk.END, "Détails des événements de roaming:\n")
            for i, (from_bssid, to_bssid, scan_num) in enumerate(bssid_changes, 1):
                self.results_text.insert(tk.END, f"{i}. Scan #{scan_num}: {from_bssid} → {to_bssid}\n")
            self.results_text.insert(tk.END, "\n")

        # Ajouter des recommandations basées sur l'analyse
        self.results_text.insert(tk.END, "Recommandations:\n")
        
        if signal_average < -70:
            self.results_text.insert(tk.END, "1. Signal faible : Optimiser le placement des points d'accès ou augmenter leur nombre pour améliorer la couverture.\n")
        
        if roaming_events > 5:
            self.results_text.insert(tk.END, "2. Nombre élevé d'événements de roaming : Augmenter le paramètre 'roaming_difference' pour éviter les effets ping-pong entre les points d'accès.\n")
        
        if interference_level in ["Modérés", "Élevés"]:
            self.results_text.insert(tk.END, "3. Interférences détectées : Reconfigurer les points d'accès pour utiliser des canaux non chevauchants (1, 6, 11 pour 2.4 GHz).\n")
        
        if variable_channels:
            self.results_text.insert(tk.END, "4. Points d'accès avec canaux variables : Vérifier la configuration des points d'accès pour éviter les changements automatiques de canaux fréquents.\n")
        
        if weak_signal_zones > 1:
            self.results_text.insert(tk.END, "5. Zones à faible signal : Ajouter des points d'accès ou des répéteurs dans ces zones pour améliorer la couverture et la qualité du signal.\n")

        self.results_text.insert(tk.END, "\n")
        
        # Ajouter les logs bruts pour plus de transparence
        self.results_text.insert(tk.END, "Résumé des données collectées:\n")
        self.results_text.insert(tk.END, f"• Nombre de scans: {len(scans_data)}\n")
        self.results_text.insert(tk.END, f"• Nombre d'entrées de données: {len(self.collected_wifi_data)}\n")
        if all_signals:
            self.results_text.insert(tk.END, f"• Plage de signaux: {min(all_signals)} à {max(all_signals)} dBm\n")
        self.results_text.insert(tk.END, "\nLogs détaillés disponibles dans l'onglet 'Tests Wi-Fi'.\n")
        
        # Activer le bouton de sauvegarde
        self.save_button.config(state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = MoxaAnalyzerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
