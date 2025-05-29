# language: PowerShell
# -*- coding: utf-8 -*-
import sys
import json
import logging
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

# Configuration sécurisée de Matplotlib avant les imports
import matplotlib
matplotlib.use('TkAgg')  # Backend sûr pour Tkinter
import matplotlib.pyplot as plt
plt.ioff()  # Mode non-interactif pour éviter les erreurs de rendu

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
import matplotlib.dates as mdates
import numpy as np
from typing import List, Optional, Dict
import os
import subprocess
import re
from dotenv import load_dotenv

# Charger automatiquement les variables d'environnement depuis un fichier .env
load_dotenv()

from network_analyzer import NetworkAnalyzer
from amr_monitor import AMRMonitor
from wifi.wifi_collector import WifiSample
from src.ai.simple_moxa_analyzer import analyze_moxa_logs
from config_manager import ConfigurationManager
from mac_tag_manager import MacTagManager

class NetworkAnalyzerUI:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("Analyseur Réseau WiFi & Moxa")

        # Optimiser la fenêtre selon la taille de l'écran
        self.optimize_window_for_screen()

        # Fenêtre de gestion des MAC
        self.mac_manager_window = None

        # Initialisation des composants
        self.analyzer = NetworkAnalyzer()
        self.samples: List[WifiSample] = []
        self.amr_ips: List[str] = []
        self.amr_monitor: Optional[AMRMonitor] = None        # Variables pour la navigation temporelle
        self.current_view_start = 0
        self.current_view_window = 300  # Nombre d'échantillons à afficher (augmenté de 100 à 300)
        self.is_real_time = True  # Mode temps réel vs navigation
        self.realtime_var = tk.BooleanVar(value=True)  # Variable pour le checkbox temps réel
        self.alert_markers = []  # Marqueurs d'alertes sur les graphiques
        self.fullscreen_window = None  # Fenêtre plein écran
        self.slider_update_in_progress = False  # Évite la récursion avec le slider

        # Configuration par défaut pour l'analyse des logs Moxa
        self.default_config = {
            "min_transmission_rate": 12,
            "max_transmission_power": 20,
            "rts_threshold": 512,
            "fragmentation_threshold": 2346,
            "roaming_mechanism": "snr",
            "roaming_difference": 8,
            "remote_connection_check": True,
            "wmm_enabled": True,
            "turbo_roaming": True,
            "ap_alive_check": True,
        }

        # Gestionnaire de configuration
        self.config_manager = ConfigurationManager(self.default_config)
        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        os.makedirs(self.config_dir, exist_ok=True)
        self.last_config_file = os.path.join(self.config_dir, "last_moxa_config.json")
        if os.path.exists(self.last_config_file):
            try:
                with open(self.last_config_file, "r", encoding="utf-8") as f:
                    self.config_manager.config = json.load(f)
            except Exception:
                pass
        self.current_config = self.config_manager.get_config()


        # Fichier pour la persistance des IPs AMR
        self.amr_ips_file = os.path.join(self.config_dir, "amr_ips.json")
        if os.path.exists(self.amr_ips_file):
            try:
                with open(self.amr_ips_file, "r", encoding="utf-8") as f:
                    self.amr_ips = json.load(f)
            except Exception:
                self.amr_ips = []

        # Manager for MAC address tags
        self.mac_manager = MacTagManager()


        # Configuration du style
        self.setup_style()

        # Création de l'interface
        self.create_interface()
        # Charger les IPs enregistrées
        for ip in self.amr_ips:
            self.amr_listbox.insert(tk.END, ip)

        # Configuration des graphiques
        self.setup_graphs()        # Variables pour les mises à jour
        self.update_interval = 1000  # ms
        self.max_samples = 500        # Historique pour l'onglet WiFi (augmenté de 100 à 500)
        self.wifi_history_entries = []
        self.max_history_entries = 5000  # Augmenté de 1000 à 5000 pour plus d'historique

    def is_portable_screen(self):
        """Détermine si l'écran est un écran portable basé sur la taille physique et le DPI"""
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        try:
            # Calculer la taille physique de l'écran
            dpi = self.master.winfo_fpixels('1i')
            diagonal_pixels = (screen_width**2 + screen_height**2)**0.5
            diagonal_inches = diagonal_pixels / dpi

            # Critères pour écran portable :
            # - Écran physique <= 16.5 pouces (laptops 15-16")
            # - OU résolution classique faible
            # - OU DPI élevé (écrans haute densité, souvent portables)
            is_portable = (
                diagonal_inches <= 16.5 or
                screen_width < 1366 or screen_height < 768 or
                dpi > 110
            )

            return is_portable, diagonal_inches, dpi

        except Exception:
            # Fallback si la détection DPI échoue
            return screen_width < 1366 or screen_height < 768, None, None

    def setup_style(self):
        """Configure le style de l'interface avec adaptation responsive"""
        style = ttk.Style()

        # Utiliser la détection centralisée
        is_small_screen, diagonal_inches, dpi = self.is_portable_screen()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Adapter la taille des polices selon l'écran
        if is_small_screen:
            title_font = ('Helvetica', 12, 'bold')
            alert_font = ('Helvetica', 10)
            stats_font = ('Helvetica', 9)
            button_font = ('Helvetica', 10)
            button_padding = 6
        else:
            title_font = ('Helvetica', 14, 'bold')
            alert_font = ('Helvetica', 12)
            stats_font = ('Helvetica', 10)
            button_font = ('Helvetica', 12)
            button_padding = 10

        style.configure("Title.TLabel", font=title_font)
        style.configure("Alert.TLabel", foreground='red', font=alert_font)
        style.configure("Stats.TLabel", font=stats_font)

        # Style pour le bouton d'analyse
        style.configure("Analyze.TButton",
                       font=button_font,
                       padding=button_padding)

        # Message d'adaptation pour l'utilisateur
        if is_small_screen:
            if diagonal_inches:
                print(f"📱 Interface adaptée pour écran portable {diagonal_inches:.1f}″ ({screen_width}x{screen_height}, DPI:{dpi:.0f})")
            else:
                print(f"📱 Interface adaptée pour petit écran ({screen_width}x{screen_height})")
        else:
            print(f"🖥️ Interface standard pour grand écran ({screen_width}x{screen_height})")

    def optimize_window_for_screen(self):
        """Optimise la taille et position de la fenêtre selon l'écran"""
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Utiliser la méthode centralisée de détection
        is_small_screen, diagonal_inches, dpi = self.is_portable_screen()

        if is_small_screen:
            # Pour les petits écrans (laptops), utiliser 95% de l'écran
            window_width = int(screen_width * 0.95)
            window_height = int(screen_height * 0.90)
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2

            self.master.geometry(f"{window_width}x{window_height}+{x}+{y}")
            if diagonal_inches:
                print(f"📱 Fenêtre optimisée: {window_width}x{window_height} pour écran portable {diagonal_inches:.1f}″ (DPI:{dpi:.0f})")
            else:
                print(f"📱 Fenêtre optimisée: {window_width}x{window_height} pour écran portable")
        else:
            # Pour les grands écrans, maximiser
            try:
                self.master.state('zoomed')  # Windows
            except tk.TclError:
                try:
                    self.master.attributes('-zoomed', True)  # Linux/Unix
                except tk.TclError:
                    # Fallback pour la compatibilité
                    self.master.geometry("1200x800")
            print(f"🖥️ Fenêtre maximisée pour grand écran")

    def create_interface(self):
        """Crée l'interface principale"""
        # Notebook pour les différentes vues
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # === Onglet WiFi ===
        self.wifi_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.wifi_frame, text="Analyse WiFi")

        # Panneau de contrôle WiFi (gauche)
        control_frame = ttk.LabelFrame(self.wifi_frame, text="Contrôles", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Boutons WiFi
        self.start_button = ttk.Button(
            control_frame,
            text="▶ Démarrer l'analyse",
            command=self.start_collection
        )
        self.start_button.pack(fill=tk.X, pady=5)

        self.stop_button = ttk.Button(
            control_frame,
            text="⏹ Arrêter l'analyse",
            command=self.stop_collection,
            state=tk.DISABLED
        )
        self.stop_button.pack(fill=tk.X, pady=5)

        # Button to manage MAC address tags
        self.mac_manage_button = ttk.Button(
            control_frame,
            text="🗂 Gérer les MAC",
            command=self.open_mac_tag_manager
        )
        self.mac_manage_button.pack(fill=tk.X, pady=5)

        # Zone de statistiques - Compacte
        stats_frame = ttk.LabelFrame(control_frame, text="Statistiques", padding=5)
        stats_frame = ttk.LabelFrame(control_frame, text="Statistiques", padding=5)
        stats_frame.pack(fill=tk.X, pady=(5, 5))

        # Zone de statistiques avec hauteur augmentée pour éviter le scroll
        self.stats_text = tk.Text(stats_frame, height=15, width=35)
        stats_scroll = ttk.Scrollbar(stats_frame, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scroll.set)
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Panneau des graphiques et alertes (droite)
        viz_frame = ttk.Frame(self.wifi_frame)
        viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Les graphiques seront ajoutés ici par setup_graphs()        # Zone d'analyse multi-onglets - Maximisée
        analysis_frame = ttk.LabelFrame(viz_frame, text="Analyse détaillée", padding=5)
        analysis_frame.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM, pady=(2, 5))

        # Notebook pour les différents affichages
        self.wifi_analysis_notebook = ttk.Notebook(analysis_frame)
        self.wifi_analysis_notebook.pack(fill=tk.BOTH, expand=True)

        # === Onglet Alertes ===
        alerts_tab = ttk.Frame(self.wifi_analysis_notebook)
        self.wifi_analysis_notebook.add(alerts_tab, text="🚨 Alertes")

        self.wifi_alert_text = tk.Text(alerts_tab, wrap=tk.WORD)
        wifi_alert_scroll = ttk.Scrollbar(alerts_tab, command=self.wifi_alert_text.yview)
        self.wifi_alert_text.configure(yscrollcommand=wifi_alert_scroll.set)
        self.wifi_alert_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        wifi_alert_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # === Onglet Historique ===
        history_tab = ttk.Frame(self.wifi_analysis_notebook)
        self.wifi_analysis_notebook.add(history_tab, text="📋 Historique")

        self.wifi_history_text = tk.Text(history_tab, wrap=tk.WORD)
        wifi_history_scroll = ttk.Scrollbar(history_tab, command=self.wifi_history_text.yview)
        self.wifi_history_text.configure(yscrollcommand=wifi_history_scroll.set)
        self.wifi_history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        wifi_history_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # === Onglet Statistiques Avancées ===
        advanced_stats_tab = ttk.Frame(self.wifi_analysis_notebook)
        self.wifi_analysis_notebook.add(advanced_stats_tab, text="📊 Stats Avancées")

        self.wifi_advanced_stats_text = tk.Text(advanced_stats_tab, wrap=tk.WORD)
        wifi_advanced_scroll = ttk.Scrollbar(advanced_stats_tab, command=self.wifi_advanced_stats_text.yview)
        self.wifi_advanced_stats_text.configure(yscrollcommand=wifi_advanced_scroll.set)
        self.wifi_advanced_stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        wifi_advanced_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # === Onglet Rapport Final ===
        final_report_tab = ttk.Frame(self.wifi_analysis_notebook)
        self.wifi_analysis_notebook.add(final_report_tab, text="📋 Rapport Final")

        self.wifi_final_report_text = tk.Text(final_report_tab, wrap=tk.WORD)
        wifi_final_scroll = ttk.Scrollbar(final_report_tab, command=self.wifi_final_report_text.yview)
        self.wifi_final_report_text.configure(yscrollcommand=wifi_final_scroll.set)
        self.wifi_final_report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        wifi_final_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # === Onglet Moxa ===
        self.moxa_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.moxa_frame, text="Analyse Moxa")

        # Zone de collage des logs - Réduite en hauteur
        input_frame = ttk.LabelFrame(self.moxa_frame, text="Collez vos logs Moxa ici :", padding=10)
        input_frame.pack(fill=tk.X, expand=False, padx=10, pady=(5, 2))

        self.moxa_input = tk.Text(input_frame, wrap=tk.WORD, height=8)
        input_scroll = ttk.Scrollbar(input_frame, command=self.moxa_input.yview)
        self.moxa_input.configure(yscrollcommand=input_scroll.set)
        self.moxa_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        input_scroll.pack(side=tk.RIGHT, fill=tk.Y)        # Zone d'édition de la configuration courante du Moxa - Réduite
        config_frame = ttk.LabelFrame(
            self.moxa_frame,
            text="Configuration Moxa actuelle (JSON) :",
            padding=10,
        )
        config_frame.pack(fill=tk.X, expand=False, padx=10, pady=(2, 2))

        self.moxa_config_text = tk.Text(config_frame, height=6, wrap=tk.WORD)
        cfg_scroll = ttk.Scrollbar(config_frame, command=self.moxa_config_text.yview)
        self.moxa_config_text.configure(yscrollcommand=cfg_scroll.set)
        self.moxa_config_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cfg_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.moxa_config_text.insert('1.0', json.dumps(self.current_config, indent=2))

        # Boutons de configuration
        config_btn_frame = ttk.Frame(self.moxa_frame)
        config_btn_frame.pack(pady=(2, 5))
        ttk.Button(config_btn_frame, text="Charger config", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="Éditer config", command=self.edit_config).pack(side=tk.LEFT, padx=5)        # Zone d'instructions personnalisées - Avec plus d'explications
        instr_frame = ttk.LabelFrame(
            self.moxa_frame,
            text="Instructions personnalisées (optionnel) - OpenAI suivra vos directives :",
            padding=10,
        )
        instr_frame.pack(fill=tk.X, expand=False, padx=10, pady=(2, 2))        # Frame pour l'aide et le bouton guide
        help_frame = ttk.Frame(instr_frame)
        help_frame.pack(fill=tk.X, pady=(0, 5))

        # Ajouter un label d'aide
        help_text = "💡 Exemples: 'Focus sur la sécurité', 'Format bullet points', 'Analyse rapide', 'Comparaison avec standard industriel', etc."
        help_label = ttk.Label(help_frame, text=help_text, font=('Arial', 9), foreground='gray')
        help_label.pack(side=tk.LEFT, anchor='w')

        # Bouton pour afficher le guide complet
        guide_button = ttk.Button(
            help_frame,
            text="📖 Guide Complet",
            command=self.show_instructions_guide,
            width=15
        )
        guide_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.custom_instr_text = tk.Text(instr_frame, height=4, wrap=tk.WORD)

        # Ajouter du texte d'exemple par défaut
        example_text = "Exemple: Concentrez-vous sur les problèmes de latence et donnez des solutions prioritaires en format liste numérotée."
        self.custom_instr_text.insert('1.0', example_text)
        self.custom_instr_text.configure(foreground='gray')

        # Gérer le focus pour effacer le texte d'exemple
        def on_focus_in(event):
            if self.custom_instr_text.get('1.0', tk.END).strip() == example_text:
                self.custom_instr_text.delete('1.0', tk.END)
                self.custom_instr_text.configure(foreground='black')

        def on_focus_out(event):
            current_text = self.custom_instr_text.get('1.0', tk.END).strip()
            if not current_text:
                self.custom_instr_text.insert('1.0', example_text)
                self.custom_instr_text.configure(foreground='gray')

        self.custom_instr_text.bind('<FocusIn>', on_focus_in)
        self.custom_instr_text.bind('<FocusOut>', on_focus_out)

        instr_scroll = ttk.Scrollbar(instr_frame, command=self.custom_instr_text.yview)
        self.custom_instr_text.configure(yscrollcommand=instr_scroll.set)
        self.custom_instr_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        instr_scroll.pack(side=tk.RIGHT, fill=tk.Y)# Bouton d'analyse
        self.analyze_button = ttk.Button(
            self.moxa_frame,
            text="🔍 Analyser les logs",
            style="Analyze.TButton",
            command=self.analyze_moxa_logs
        )
        self.analyze_button.pack(pady=(5, 8))

        # Zone des résultats - Agrandie pour prendre tout l'espace restant
        results_frame = ttk.LabelFrame(self.moxa_frame, text="Résultats de l'analyse :", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 5))

        self.moxa_results = tk.Text(results_frame, wrap=tk.WORD)
        results_scroll = ttk.Scrollbar(results_frame, command=self.moxa_results.yview)
        self.moxa_results.configure(yscrollcommand=results_scroll.set)
        self.moxa_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bouton d'export
        self.export_button = ttk.Button(
            self.moxa_frame,
            text="💾 Exporter l'analyse",
            command=self.export_data,
            state=tk.DISABLED
        )
        self.export_button.pack(pady=5)

        # === Onglet Monitoring AMR ===
        self.amr_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.amr_frame, text="Monitoring AMR")

        amr_control = ttk.LabelFrame(self.amr_frame, text="Adresses IP", padding=10)
        amr_control.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        self.amr_ip_var = tk.StringVar()
        ttk.Entry(amr_control, textvariable=self.amr_ip_var).pack(fill=tk.X, pady=2)
        ttk.Button(amr_control, text="Ajouter", command=self.add_amr_ip).pack(fill=tk.X, pady=2)
        ttk.Button(amr_control, text="Supprimer", command=self.remove_amr_ip).pack(fill=tk.X, pady=2)

        self.amr_listbox = tk.Listbox(amr_control, height=6)
        self.amr_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        self.amr_start_button = ttk.Button(amr_control, text="▶ Démarrer", command=self.start_amr_monitoring)
        self.amr_start_button.pack(fill=tk.X, pady=2)
        self.amr_stop_button = ttk.Button(amr_control, text="⏹ Arrêter", command=self.stop_amr_monitoring, state=tk.DISABLED)
        self.amr_stop_button.pack(fill=tk.X, pady=2)
        ttk.Button(amr_control, text="Traceroute", command=self.traceroute_selected_ip).pack(fill=tk.X, pady=2)

        status_frame = ttk.LabelFrame(self.amr_frame, text="Statut", padding=10)
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.amr_status_text = tk.Text(status_frame, height=10, wrap=tk.WORD)
        status_scroll = ttk.Scrollbar(status_frame, command=self.amr_status_text.yview)
        self.amr_status_text.configure(yscrollcommand=status_scroll.set)
        self.amr_status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_graphs(self):
        """Configure les graphiques avec navigation simplifiée et intuitive"""

        # Variables de navigation
        self.max_samples = 500  # Consistant avec la valeur du constructeur
        self.current_view_start = 0
        self.current_view_window = 300  # Consistant avec la valeur du constructeur
        self.is_real_time = True
        self.alert_markers = []
        
        # Variables pour zoom temporel
        self.temporal_view = "5min"  # Options: "1min", "5min", "total"
        self.update_interval = 1000  # 1 seconde

        # Frame principal pour les graphiques
        graph_main_frame = ttk.Frame(self.wifi_frame)
        graph_main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)        # === CONTRÔLES RESPONSIFS ===
        nav_frame = ttk.LabelFrame(graph_main_frame, text="🎯 Navigation", padding=5)
        nav_frame.pack(fill=tk.X, pady=(0, 5))

        # Utiliser la détection centralisée pour cohérence
        is_small_screen, diagonal_inches, dpi = self.is_portable_screen()

        # Mode de vue et plein écran (toujours en haut)
        view_frame = ttk.Frame(nav_frame)
        view_frame.pack(fill=tk.X, pady=2)

        self.view_mode = tk.StringVar(value="direct")
        ttk.Radiobutton(view_frame, text="📡 Suivi Direct", variable=self.view_mode,
                       value="direct", command=self.change_view_mode).pack(side=tk.LEFT, padx=8)
        ttk.Radiobutton(view_frame, text="📊 Analyse", variable=self.view_mode,
                       value="analysis", command=self.change_view_mode).pack(side=tk.LEFT, padx=8)        # Bouton plein écran
        self.fullscreen_button = ttk.Button(
            view_frame,
            text="🖥️ Plein Écran",
            command=self.open_fullscreen_graphs
        )
        self.fullscreen_button.pack(side=tk.RIGHT, padx=8)

        # Frame pour les contrôles de zoom temporel
        temporal_frame = ttk.Frame(nav_frame)
        temporal_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(temporal_frame, text="⏱️ Zoom temporel:").pack(side=tk.LEFT, padx=5)
        
        self.temporal_view_var = tk.StringVar(value="5min")
        
        ttk.Radiobutton(temporal_frame, text="1 min", variable=self.temporal_view_var,
                       value="1min", command=self.change_temporal_view).pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(temporal_frame, text="5 min", variable=self.temporal_view_var,
                       value="5min", command=self.change_temporal_view).pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(temporal_frame, text="Total", variable=self.temporal_view_var,
                       value="total", command=self.change_temporal_view).pack(side=tk.LEFT, padx=3)

        if is_small_screen:
            # MISE EN PAGE RESPONSIVE POUR PETITS ÉCRANS
            # Ligne 1: Navigation par alertes
            alert_frame = ttk.Frame(nav_frame)
            alert_frame.pack(fill=tk.X, pady=2)

            ttk.Button(alert_frame, text="🚨 Prochaine alerte",
                      command=self.go_to_next_alert).pack(side=tk.LEFT, padx=3)
            ttk.Button(alert_frame, text="🚨 Alerte précédente",
                      command=self.go_to_previous_alert).pack(side=tk.LEFT, padx=3)

            # Ligne 2: Navigation par qualité signal
            signal_frame = ttk.Frame(nav_frame)
            signal_frame.pack(fill=tk.X, pady=2)

            ttk.Button(signal_frame, text="📈 Meilleur signal",
                      command=self.go_to_signal_peak).pack(side=tk.LEFT, padx=3)
            ttk.Button(signal_frame, text="📉 Signal faible",
                      command=self.go_to_signal_low).pack(side=tk.LEFT, padx=3)

            # Ligne 3: Contrôles de base
            basic_frame = ttk.Frame(nav_frame)
            basic_frame.pack(fill=tk.X, pady=2)

            ttk.Button(basic_frame, text="⏮️ Début", command=self.go_to_start).pack(side=tk.LEFT, padx=3)
            ttk.Button(basic_frame, text="⏭️ Fin/Live", command=self.go_live).pack(side=tk.LEFT, padx=3)

        else:
            # MISE EN PAGE NORMALE POUR GRANDS ÉCRANS
            # Navigation par événements
            event_frame = ttk.Frame(nav_frame)
            event_frame.pack(fill=tk.X, pady=5)

            # Navigation par alertes
            ttk.Button(event_frame, text="🚨 Prochaine alerte",
                      command=self.go_to_next_alert).pack(side=tk.LEFT, padx=5)
            ttk.Button(event_frame, text="🚨 Alerte précédente",
                      command=self.go_to_previous_alert).pack(side=tk.LEFT, padx=5)

            # Séparateur visuel
            ttk.Separator(event_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)

            # Navigation par pics/creux
            ttk.Button(event_frame, text="📈 Meilleur signal",
                      command=self.go_to_signal_peak).pack(side=tk.LEFT, padx=5)
            ttk.Button(event_frame, text="📉 Signal faible",
                      command=self.go_to_signal_low).pack(side=tk.LEFT, padx=5)

            # Contrôles de base
            basic_frame = ttk.Frame(nav_frame)
            basic_frame.pack(fill=tk.X, pady=5)

            ttk.Button(basic_frame, text="⏮️ Début", command=self.go_to_start).pack(side=tk.LEFT, padx=2)
            ttk.Button(basic_frame, text="⏭️ Fin/Live", command=self.go_live).pack(side=tk.LEFT, padx=2)

        # Info contextuelle (adaptée selon la taille)
        context_text = "📡 Mode suivi direct - Navigation adaptée" if is_small_screen else "📡 Mode suivi direct - Utilisez la souris pour naviguer sur les graphiques"
        self.context_label = ttk.Label(nav_frame, text=context_text)
        self.context_label.pack(pady=3)

        # === GRAPHIQUES ===
        # Figure principale
        self.fig = Figure(figsize=(10, 6))
        self.fig.subplots_adjust(hspace=0.3)

        # Graphique du signal avec marqueurs d'alertes
        self.ax1 = self.fig.add_subplot(211)
        self.ax1.set_title("Force du signal WiFi")
        self.ax1.set_ylabel("Signal (dBm)")
        self.ax1.grid(True, alpha=0.3)
        self.signal_line, = self.ax1.plot([], [], 'b-', linewidth=2, label="Signal")
        self.ax1.set_ylim(-90, -30)
        self.ax1.legend()

        # Graphique de la qualité avec marqueurs d'alertes
        self.ax2 = self.fig.add_subplot(212)
        self.ax2.set_title("Qualité de la connexion")
        self.ax2.set_ylabel("Qualité (%)")
        self.ax2.set_xlabel("Temps (échantillons)")
        self.ax2.grid(True, alpha=0.3)
        self.quality_line, = self.ax2.plot([], [], 'g-', linewidth=2, label="Qualité")
        self.ax2.set_ylim(0, 100)
        self.ax2.legend()

        # Canvas Matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Toolbar de navigation matplotlib (pour zoom/pan à la souris)
        toolbar_frame = ttk.Frame(graph_main_frame)
        toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Raccourcis clavier simples
        self.master.bind('<Left>', lambda e: self.go_to_previous_alert())
        self.master.bind('<Right>', lambda e: self.go_to_next_alert())
        self.master.bind('<Home>', lambda e: self.go_to_start())
        self.master.bind('<End>', lambda e: self.go_live())
        self.master.focus_set()

    def start_collection(self):
        """Démarre la collecte WiFi"""
        try:
            if self.analyzer.start_analysis():
                self.samples = []
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                self.update_data()
                self.update_status("Collection en cours...")
        except Exception as e:
            self.show_error(f"Erreur au démarrage: {str(e)}")

    def stop_collection(self):
        """Arrête la collecte WiFi"""
        self.analyzer.stop_analysis()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.export_button.config(state=tk.NORMAL)
        self.update_status("Collection arrêtée")

        # Générer le rapport final
        self.generate_final_network_report()

    def analyze_moxa_logs(self):
        """Analyse les logs Moxa collés avec OpenAI"""
        try:
            logs = self.moxa_input.get('1.0', tk.END).strip()
            if not logs:
                messagebox.showwarning(
                    "Analyse impossible",
                    "Veuillez coller des logs Moxa à analyser"
                )
                return            # Vérifier la clé API OpenAI dans l'environnement
            api_key = os.getenv("OPENAI_API_KEY")
            print(f"Valeur de OPENAI_API_KEY: {api_key[:10]}..." if api_key else "Clé API non trouvée")

            if not api_key:
                # Recharger explicitement le fichier .env
                from dotenv import load_dotenv
                env_file = os.path.join(os.path.dirname(__file__), '.env')
                if os.path.exists(env_file):
                    load_dotenv(env_file)
                    api_key = os.getenv("OPENAI_API_KEY")
                    print(f"Après rechargement: {api_key[:10]}..." if api_key else "Toujours pas de clé")

                if not api_key:
                    messagebox.showerror(
                        "Clé API manquante",
                        "La variable d'environnement OPENAI_API_KEY doit être définie pour utiliser l'analyse OpenAI."
                    )
                    return

            # Mise à jour de l'interface
            self.moxa_results.delete('1.0', tk.END)
            self.moxa_results.insert('1.0', "🔄 Analyse en cours avec OpenAI...\n\n")
            self.analyze_button.config(state=tk.DISABLED)
            self.moxa_results.update()

            # Récupérer la configuration depuis la zone de texte
            try:
                config_text = self.moxa_config_text.get('1.0', tk.END).strip()
                if config_text:
                    self.current_config = json.loads(config_text)
            except json.JSONDecodeError:
                messagebox.showerror(
                    "Configuration invalide",
                    "La configuration Moxa n'est pas un JSON valide."
                )
                return

            # Récupérer les instructions personnalisées
            custom_instr = self.custom_instr_text.get('1.0', tk.END).strip()

            # Appel à l'API OpenAI avec la configuration courante et instructions optionnelles
            analysis = analyze_moxa_logs(logs, self.current_config, custom_instr)

            if analysis:
                self.moxa_results.delete('1.0', tk.END)

                # Configuration des styles de texte
                self.moxa_results.tag_configure("title", font=("Arial", 12, "bold"))
                self.moxa_results.tag_configure("section", font=("Arial", 10, "bold"))
                self.moxa_results.tag_configure("normal", font=("Arial", 10))
                self.moxa_results.tag_configure("alert", foreground="red")
                self.moxa_results.tag_configure("success", foreground="green")
                self.moxa_results.tag_configure("warning", foreground="orange")

                # Affichage de l'analyse avec mise en forme
                self.moxa_results.insert('end', "Analyse OpenAI des Logs Moxa\n\n", "title")

                # Formater et afficher la réponse d'OpenAI
                self.format_and_display_ai_analysis(analysis)

                # Activer le bouton d'export
                self.export_button.config(state=tk.NORMAL)
                messagebox.showinfo("Succès", "Analyse complétée par OpenAI !")
                self.save_last_config()
            else:
                self.moxa_results.insert('1.0', "❌ Aucun résultat d'analyse\n")

        except Exception as e:
            self.show_error(f"Erreur d'analyse: {str(e)}")
        finally:
            self.analyze_button.config(state=tk.NORMAL)


    def load_config(self):
        """Charge un fichier de configuration JSON."""
        filepath = filedialog.askopenfilename(
            initialdir=self.config_dir,
            filetypes=[("JSON", "*.json")],
            title="Charger une configuration"
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.config_manager.config = json.load(f)
                self.current_config = self.config_manager.get_config()
                self.moxa_config_text.delete('1.0', tk.END)
                self.moxa_config_text.insert('1.0', json.dumps(self.current_config, indent=2))
                messagebox.showinfo("Configuration", f"Configuration chargée depuis {filepath}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger la configuration:\n{e}")

    def edit_config(self):
        """Affiche un formulaire pour modifier la configuration."""
        dialog = tk.Toplevel(self.master)
        dialog.title("Éditer la configuration")
        entries = {}

        for row, (key, value) in enumerate(self.config_manager.get_config().items()):
            ttk.Label(dialog, text=key).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value=str(value))
            ttk.Entry(dialog, textvariable=var, width=20).grid(row=row, column=1, padx=5, pady=2)
            entries[key] = var

        def save():
            for k, v in entries.items():
                val = v.get()
                if val.lower() in ("true", "false"):
                    parsed = val.lower() == "true"
                else:
                    try:
                        parsed = int(val)
                    except ValueError:
                        try:
                            parsed = float(val)
                        except ValueError:
                            parsed = val
                self.config_manager.update_config(k, parsed)
            self.current_config = self.config_manager.get_config()
            self.moxa_config_text.delete('1.0', tk.END)
            self.moxa_config_text.insert('1.0', json.dumps(self.current_config, indent=2))
            dialog.destroy()

        ttk.Button(dialog, text="OK", command=save).grid(row=len(entries), column=0, padx=5, pady=10)
        ttk.Button(dialog, text="Annuler", command=dialog.destroy).grid(row=len(entries), column=1, padx=5, pady=10)

    def save_last_config(self):
        """Sauvegarde la configuration actuelle pour réutilisation."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.last_config_file, "w", encoding="utf-8") as f:
                json.dump(self.config_manager.get_config(), f, indent=2)
        except Exception:
            pass

    def format_and_display_ai_analysis(self, analysis: str):
        """Formate et affiche l'analyse OpenAI dans l'interface"""
        try:
            # Essayer de parser comme JSON d'abord
            try:
                data = json.loads(analysis)
                self.display_structured_analysis(data)
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON, afficher comme texte formaté
                self.display_text_analysis(analysis)
        except Exception as e:
            # En cas d'erreur, afficher le texte brut
            self.moxa_results.insert('end', analysis)

    def display_structured_analysis(self, data: dict):
        """Affiche une analyse structurée (JSON)"""
        if "score_global" in data:
            score = data["score_global"]
            self.moxa_results.insert('end', f"Score Global: {score}/100\n", "title")

            if score >= 70:
                self.moxa_results.insert('end', "✅ Configuration adaptée\n\n", "success")
            elif score >= 50:
                self.moxa_results.insert('end', "⚠️ Améliorations possibles\n\n", "warning")
            else:
                self.moxa_results.insert('end', "❌ Optimisation nécessaire\n\n", "alert")

        if "problemes" in data:
            self.moxa_results.insert('end', "Problèmes Détectés:\n", "section")
            for prob in data["problemes"]:
                self.moxa_results.insert('end', f"• {prob}\n", "normal")
            self.moxa_results.insert('end', "\n")

        if "recommendations" in data:
            self.moxa_results.insert('end', "Recommandations:\n", "section")
            for rec in data["recommendations"]:
                if isinstance(rec, dict):
                    self.moxa_results.insert('end', f"• Problème: {rec.get('probleme', '')}\n", "normal")
                    self.moxa_results.insert('end', f"  Solution: {rec.get('solution', '')}\n\n", "normal")
                else:
                    self.moxa_results.insert('end', f"• {rec}\n", "normal")
            self.moxa_results.insert('end', "\n")

        if "analyse_detaillee" in data:
            self.moxa_results.insert('end', "Analyse Détaillée:\n", "section")
            self.moxa_results.insert('end', f"{data['analyse_detaillee']}\n\n", "normal")

        if "conclusion" in data:
            self.moxa_results.insert('end', "Conclusion:\n", "section")
            self.moxa_results.insert('end', f"{data['conclusion']}\n", "normal")

    def display_text_analysis(self, text: str):
        """Affiche une analyse en format texte"""
        # Diviser le texte en sections basées sur les numéros ou les titres communs
        sections = text.split('\n\n')

        for section in sections:
            if section.strip():
                # Détecter si c'est un titre
                if any(keyword in section.lower() for keyword in ['problèmes:', 'recommandations:', 'analyse:', 'conclusion:', 'impact:']):
                    self.moxa_results.insert('end', f"\n{section}\n", "section")
                else:
                    self.moxa_results.insert('end', f"{section}\n", "normal")

        self.moxa_results.see('1.0')  # Remonter au début

    def prompt_for_tag(self, mac_address):
        """Prompt the user to provide a tag for a new MAC address"""
        # Don't prompt if MAC is invalid or None
        if not mac_address or mac_address == "Unknown":
            return

        # Use the simpledialog module to ask for input
        tag = simpledialog.askstring(
            "Nouveau point d'accès détecté",
            f"Saisissez un nom/tag pour le point d'accès {mac_address}:",
            parent=self.master
        )

        # If the user provided a tag, save it
        if tag:
            self.mac_manager.add_tag(mac_address, tag)
            return tag

        return None

    def update_data(self):
        """Met à jour les données en temps réel"""
        if not self.analyzer.is_collecting:
            return

        sample = self.analyzer.wifi_collector.collect_sample()
        if sample:
            self.samples.append(sample)
            # Prompt for tag if new access point detected
            if sample.bssid and not self.mac_manager.get_tag(sample.bssid):
                self.prompt_for_tag(sample.bssid)
            self.update_display()
            self.update_stats()
            self.check_wifi_issues(sample)

        self.master.after(self.update_interval, self.update_data)

    def check_wifi_issues(self, sample: WifiSample):
        """Vérifie et affiche les problèmes WiFi"""
        alerts = []
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Force du signal - Seuils réalistes alignés avec les standards WiFi
        if sample.signal_strength < -85:
            alerts.append(f"🔴 Signal CRITIQUE : {sample.signal_strength} dBm")
        elif sample.signal_strength < -80:
            alerts.append(f"⚠️ Signal faible : {sample.signal_strength} dBm")

        # Qualité - Seuils réalistes pour les environnements industriels
        if sample.quality < 20:
            alerts.append(f"🔴 Qualité CRITIQUE : {sample.quality}%")
        elif sample.quality < 40:
            alerts.append(f"⚠️ Qualité faible : {sample.quality}%")        # Débits - Seuils réalistes et intelligents
        try:
            tx_rate = int(sample.raw_data.get('TransmitRate', '0 Mbps').split()[0])
            rx_rate = int(sample.raw_data.get('ReceiveRate', '0 Mbps').split()[0])

            # Seuils adaptatifs et réalistes
            min_tx_critical = 10  # TX critique si < 10 Mbps
            min_rx_critical = 2   # RX critique si < 2 Mbps
            min_tx_warning = 50   # TX warning si < 50 Mbps
            min_rx_warning = 5    # RX warning si < 5 Mbps

            # Alerte critique seulement si les deux débits sont vraiment problématiques
            if tx_rate < min_tx_critical and rx_rate < min_rx_critical:
                alerts.append(
                    f"🔴 Débits CRITIQUES :\n"
                    f"   TX: {tx_rate} Mbps, RX: {rx_rate} Mbps"
                )
            # Alerte warning si un seul débit est problématique
            elif tx_rate < min_tx_warning and rx_rate < min_rx_warning:
                alerts.append(
                    f"⚠️ Débits faibles :\n"
                    f"   TX: {tx_rate} Mbps, RX: {rx_rate} Mbps"
                )
        except (ValueError, IndexError, KeyError):
            pass

        # Mise à jour onglet Alertes        if alerts:
            msg = f"Position au {timestamp} :\n"
            msg += "\n".join(alerts)
            self.wifi_alert_text.delete('1.0', tk.END)
            self.wifi_alert_text.insert('1.0', msg)

        # Ajouter à l'historique (même si pas d'alertes)
        self.add_to_wifi_history(sample, alerts, timestamp)

        # Mettre à jour les stats avancées
        self.update_advanced_wifi_stats()

    def add_to_wifi_history(self, sample: WifiSample, alerts: list, timestamp: str):
        """Ajoute un échantillon à l'historique WiFi"""
        entry = {
            'timestamp': timestamp,
            'signal': sample.signal_strength,
            'quality': sample.quality,
            'bssid': sample.bssid if hasattr(sample, 'bssid') else "Unknown",
            'alerts': alerts.copy() if alerts else []
        }

        self.wifi_history_entries.append(entry)

        # Limiter la taille de l'historique
        if len(self.wifi_history_entries) > self.max_history_entries:
            self.wifi_history_entries = self.wifi_history_entries[-self.max_history_entries:]        # Mettre à jour l'affichage de l'historique
        self.update_wifi_history_display()

    def update_wifi_history_display(self):
        """Met à jour l'affichage de l'historique WiFi"""
        if not hasattr(self, 'wifi_history_text'):
            return

        try:            # Limiter l'affichage aux 300 dernières entrées pour les performances
            recent_entries = self.wifi_history_entries[-300:]

            history_text = "=== Historique WiFi (300 dernières entrées) ===\n\n"

            for entry in reversed(recent_entries):  # Plus récent en premier
                history_text += f"[{entry['timestamp']}] "
                history_text += f"Signal: {entry['signal']} dBm, "
                history_text += f"Qualité: {entry['quality']}%"

                # Ajouter le BSSID si disponible
                if entry.get('bssid') and entry['bssid'] != "Unknown":
                    tag = self.mac_manager.get_tag(entry['bssid'])
                    tag_str = f" ({tag})" if tag else ""
                    history_text += f", AP: {entry['bssid']}{tag_str}"

                history_text += "\n"

                if entry['alerts']:
                    for alert in entry['alerts']:
                        history_text += f"  → {alert}\n"

                history_text += "\n"

            self.wifi_history_text.delete('1.0', tk.END)
            self.wifi_history_text.insert('1.0', history_text)

        except Exception as e:
            logging.error(f"Erreur dans update_wifi_history_display: {str(e)}")

    def generate_final_network_report(self):
        """Génère et affiche le rapport final d'analyse réseau"""
        if not hasattr(self, 'wifi_final_report_text'):
            return

        try:
            if not self.samples:
                report = "❌ Aucune donnée disponible pour générer un rapport.\n"
                report += "Veuillez d'abord effectuer une analyse WiFi."
            else:
                # Utiliser l'analyzer pour obtenir un rapport combiné
                combined_report = self.analyzer.get_combined_report()

                report = "📋 RAPPORT FINAL D'ANALYSE RÉSEAU\n"
                report += "=" * 50 + "\n\n"
                report += f"📅 Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report += f"📊 Échantillons analysés : {len(self.samples)}\n\n"

                # Section WiFi
                if 'wifi_analysis' in combined_report and combined_report['wifi_analysis']:
                    wifi = combined_report['wifi_analysis']
                    report += "📶 ANALYSE WIFI\n"
                    report += "-" * 20 + "\n"

                    signal = wifi.get('signal_strength', {})
                    if signal:
                        report += f"Signal moyen : {signal.get('average', 0):.1f} dBm\n"
                        report += f"Signal min/max : {signal.get('min', 0):.1f} / {signal.get('max', 0):.1f} dBm\n"

                    quality = wifi.get('quality', {})
                    if quality:
                        report += f"Qualité connexion : {quality.get('connection', 0):.1f}%\n"
                        report += f"Stabilité signal : {quality.get('stability', 0):.1f}%\n"

                    dropouts = wifi.get('dropouts', 0)
                    report += f"Déconnexions : {dropouts}\n\n"

                # Section recommandations
                if 'recommendations' in combined_report and combined_report['recommendations']:
                    report += "💡 RECOMMANDATIONS\n"
                    report += "-" * 20 + "\n"
                    for i, rec in enumerate(combined_report['recommendations'], 1):
                        report += f"{i}. {rec}\n"
                    report += "\n"

                # Score global calculé
                if self.samples:
                    avg_signal = sum(s.signal_strength for s in self.samples) / len(self.samples)
                    avg_quality = sum(s.quality for s in self.samples) / len(self.samples)

                    # Calcul du score global (0-100)
                    signal_score = max(0, min(100, (avg_signal + 100) * 2))  # -100 dBm = 0%, -50 dBm = 100%
                    quality_score = avg_quality
                    global_score = (signal_score + quality_score) / 2

                    report += "🎯 SCORE GLOBAL\n"
                    report += "-" * 20 + "\n"
                    report += f"Score final : {global_score:.1f}/100\n"

                    if global_score >= 80:
                        report += "✅ Excellent - Réseau parfaitement optimisé\n"
                    elif global_score >= 60:
                        report += "🟡 Bon - Quelques améliorations possibles\n"
                    elif global_score >= 40:
                        report += "🟠 Moyen - Optimisations recommandées\n"
                    else:
                        report += "🔴 Critique - Intervention urgente requise\n"

            self.wifi_final_report_text.delete('1.0', tk.END)
            self.wifi_final_report_text.insert('1.0', report)

            # Basculer vers l'onglet du rapport
            if hasattr(self, 'wifi_analysis_notebook'):
                for i in range(self.wifi_analysis_notebook.index('end')):
                    if 'rapport' in self.wifi_analysis_notebook.tab(i, 'text').lower():
                        self.wifi_analysis_notebook.select(i)
                        break

            logging.info("Rapport final généré avec succès")

        except Exception as e:
            error_msg = f"Erreur lors de la génération du rapport: {str(e)}"
            logging.error(error_msg)
            if hasattr(self, 'wifi_final_report_text'):
                self.wifi_final_report_text.delete('1.0', tk.END)
                self.wifi_final_report_text.insert('1.0', f"❌ {error_msg}")

    def go_to_end(self):
        """Va à la fin des données (derniers échantillons)"""
        try:
            if self.samples:
                self.is_real_time = False
                self.realtime_var.set(False)
                self.current_view_start = max(0, len(self.samples) - self.current_view_window)
                self.update_display()
                if hasattr(self, 'context_label'):
                    self.context_label.config(text="📊 Fin de l'analyse - Dernières données collectées")
        except Exception as e:
            logging.error(f"Erreur dans go_to_end: {str(e)}")

    def update_display(self):
        """Met à jour les graphiques avec navigation temporelle"""
        if not self.samples:
            return

        try:            # Créer une copie locale des échantillons pour éviter les problèmes
            # de concurrence lorsque la liste est modifiée pendant la navigation
            samples_snapshot = list(self.samples)

            # Ajuster current_view_window pour la vue "total"
            if self.temporal_view == "total":
                self.current_view_window = len(samples_snapshot) if samples_snapshot else 300

            # Déterminer la plage d'affichage selon le mode
            if self.is_real_time:
                # Mode temps réel : afficher les derniers échantillons
                start_idx = max(0, len(samples_snapshot) - self.current_view_window)
                end_idx = len(samples_snapshot)
            else:
                # Mode navigation : afficher la fenêtre sélectionnée
                start_idx = self.current_view_start
                # S'assurer qu'on ne dépasse pas la fin des données
                end_idx = min(len(samples_snapshot), start_idx + self.current_view_window)

                # Si on essaie d'afficher plus d'échantillons qu'il n'y en a,
                # ajuster le début pour montrer les derniers échantillons disponibles
                if end_idx - start_idx < self.current_view_window and end_idx == len(samples_snapshot):
                    start_idx = max(0, end_idx - self.current_view_window)

            # Extraire les données à afficher
            display_samples = samples_snapshot[start_idx:end_idx]
            if not display_samples:
                return

            signals = [s.signal_strength for s in display_samples]
            qualities = [s.quality for s in display_samples]
            x_data = range(len(signals))

            # Vérifier que nous avons des données valides
            if not signals or not qualities:
                return

            # Mise à jour des lignes principales avec protection
            try:
                self.signal_line.set_data(x_data, signals)
                self.quality_line.set_data(x_data, qualities)

                # Mise à jour des axes avec valeurs valides
                if len(signals) > 0:
                    self.ax1.set_xlim(0, max(1, len(signals)))
                    self.ax2.set_xlim(0, max(1, len(qualities)))

                # Marquer les alertes sur les graphiques
                self.mark_alerts_on_graphs()

                # Rafraîchissement avec gestion d'erreur
                self.canvas.draw_idle()  # Utiliser draw_idle() au lieu de draw()

            except Exception as graph_error:
                logging.warning(f"Erreur lors de la mise à jour des graphiques: {graph_error}")

            # Mettre à jour les graphiques plein écran si ouverts
            if hasattr(self, 'fullscreen_window') and self.fullscreen_window and self.fullscreen_window.winfo_exists():
                try:
                    self.update_fullscreen_display()
                except Exception as fs_error:
                    logging.warning(f"Erreur lors de la mise à jour plein écran: {fs_error}")

            # Mettre à jour les infos de position
            self.update_status_info()

        except Exception as e:
            logging.error(f"Erreur générale dans update_display: {e}")
            # Continuer sans faire crasher l'application

    def update_status_info(self):
        """Met à jour l'information de statut simple"""
        if not hasattr(self, 'context_label'):
            return

        if self.is_real_time:
            self.context_label.config(text="📡 Mode suivi direct - Les données s'affichent en temps réel")
        else:
            total = len(self.samples) if self.samples else 0
            if total > 0:
                current_pos = self.current_view_start + (self.current_view_window // 2)
                time_info = self._get_relative_time(current_pos)
                self.context_label.config(text=f"📊 Mode analyse - Position: {time_info}")
            else:
                self.context_label.config(text="📊 Mode analyse - Aucune donnée")

    def mark_alerts_on_graphs(self):
        """Marque les points d'alerte sur les graphiques"""
        try:
            # Effacer les anciens marqueurs
            for marker in self.alert_markers:
                try:
                    marker.remove()
                except:
                    pass
            self.alert_markers = []

            if not self.samples:
                return

            # Créer une copie locale des échantillons pour éviter les problèmes de concurrence
            samples_snapshot = list(self.samples)

            # Déterminer la plage d'affichage
            if self.is_real_time:
                start_idx = max(0, len(samples_snapshot) - self.current_view_window)
            else:
                start_idx = self.current_view_start

            # S'assurer que les indices sont valides
            end_idx = min(len(samples_snapshot), start_idx + self.current_view_window)

            # Marquer les points avec alertes
            for i, sample in enumerate(samples_snapshot[start_idx:end_idx]):
                has_alert = False                # Vérifier les différents types d'alertes
                if sample.signal_strength < -85:
                    has_alert = True
                elif sample.quality < 20:
                    has_alert = True
                elif self._check_rate_alerts(sample):
                    has_alert = True
                if has_alert:
                    # Marquer sur les deux graphiques
                    marker1 = self.ax1.axvline(x=i, color='red', alpha=0.5, linewidth=1)
                    marker2 = self.ax2.axvline(x=i, color='red', alpha=0.5, linewidth=1)
                    self.alert_markers.extend([marker1, marker2])
        except Exception as e:
            logging.error(f"Erreur dans mark_alerts_on_graphs: {str(e)}")
            # Éviter le crash en cas d'erreur

    def update_stats(self):
        """Met à jour les statistiques dans l'interface"""
        if not self.samples:
            return        # Calcul des statistiques
        current_sample = self.samples[-1]  # Dernier échantillon
        signal_values = [s.signal_strength for s in self.samples[-100:]]  # 100 derniers échantillons (augmenté de 20 à 100)
        quality_values = [s.quality for s in self.samples[-100:]]

        # Stats WiFi actuelles
        stats_text = "=== État Actuel ===\n"
        stats_text += f"Signal : {current_sample.signal_strength} dBm\n"
        stats_text += f"Qualité: {current_sample.quality}%\n"

        # Stats moyennes (100 derniers échantillons)
        avg_signal = sum(signal_values) / len(signal_values)
        avg_quality = sum(quality_values) / len(quality_values)
        stats_text += "\n=== Moyenne (100 éch.) ===\n"
        stats_text += f"Signal : {avg_signal:.1f} dBm\n"
        stats_text += f"Qualité: {avg_quality:.1f}%\n"

        # Débits actuels
        try:
            tx_rate = int(current_sample.raw_data.get('TransmitRate', '0 Mbps').split()[0])
            rx_rate = int(current_sample.raw_data.get('ReceiveRate', '0 Mbps').split()[0])
            stats_text += "\n=== Débits ===\n"
            stats_text += f"TX: {tx_rate} Mbps\n"
            stats_text += f"RX: {rx_rate} Mbps"
        except (ValueError, IndexError, KeyError):
            pass        # Mise à jour du texte
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0', stats_text)

    def export_data(self):
        """Exporte les données d'analyse"""
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("Fichiers JSON", "*.json")],
                title="Exporter l'analyse"
            )
            if filepath:
                self.analyzer.export_data(filepath)
                messagebox.showinfo(
                    "Export réussi",
                    f"Les données ont été exportées vers :\n{filepath}"
                )
        except Exception as e:
            self.show_error(f"Erreur lors de l'export: {str(e)}")

    def update_status(self, message: str):
        """Met à jour les infos de statut"""
        current_time = datetime.now().strftime("%H:%M:%S")

        # Mettre à jour l'onglet Alertes avec le message de statut
        status_msg = f"{current_time} - {message}\n"
        self.wifi_alert_text.insert('1.0', status_msg)

        # Ajouter aussi à l'historique si c'est important
        if any(keyword in message.lower() for keyword in ['démarr', 'arrêt', 'erreur', 'succès']):
            entry = {
                'timestamp': current_time,
                'signal': 0,
                'quality': 0,
                'alerts': [f"📢 {message}"]
            }
            self.wifi_history_entries.append(entry)
            self.update_wifi_history_display()

    def show_error(self, error_message: str):
        """Affiche une erreur"""
        messagebox.showerror("Erreur", error_message)
        # Ajouter directement à l'historique sans appeler update_status pour éviter la récursion
        current_time = datetime.now().strftime("%H:%M:%S")
        self.wifi_alert_text.insert('1.0', f"{current_time} - ERREUR: {error_message}\n")

        # Ajouter à l'historique
        entry = {
            'timestamp': current_time,
            'signal': 0,
            'quality': 0,
            'alerts': [f"🔴 ERREUR: {error_message}"]
        }
        self.wifi_history_entries.append(entry)
        self.update_wifi_history_display()

    # ===== Fonctions Monitoring AMR =====
    def add_amr_ip(self) -> None:
        ip = self.amr_ip_var.get().strip()
        if ip and ip not in self.amr_ips:
            self.amr_ips.append(ip)
            self.amr_listbox.insert(tk.END, ip)
            self.save_amr_ips()
        self.amr_ip_var.set("")

    def remove_amr_ip(self) -> None:
        selection = self.amr_listbox.curselection()
        for index in reversed(selection):
            ip = self.amr_listbox.get(index)
            self.amr_listbox.delete(index)
            if ip in self.amr_ips:
                self.amr_ips.remove(ip)
        if selection:            self.save_amr_ips()

    def save_amr_ips(self) -> None:
        try:
            with open(self.amr_ips_file, "w", encoding="utf-8") as f:
                json.dump(self.amr_ips, f, indent=2)
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des IPs AMR: {e}")

    def start_amr_monitoring(self) -> None:
        """Démarre le monitoring AMR"""
        self.amr_monitor = AMRMonitor(self.amr_ips)
        self.amr_monitor.start(callback=self.update_amr_status)
        self.amr_start_button.config(state=tk.DISABLED)
        self.amr_stop_button.config(state=tk.NORMAL)
        self.update_status("Monitoring AMR démarré")

    def stop_amr_monitoring(self) -> None:
        """Arrête le monitoring AMR"""
        if self.amr_monitor:
            self.amr_monitor.stop()
            self.amr_monitor = None
        self.amr_start_button.config(state=tk.NORMAL)
        self.amr_stop_button.config(state=tk.DISABLED)
        self.update_status("Monitoring AMR arrêté")

    def traceroute_selected_ip(self) -> None:
        selection = self.amr_listbox.curselection()
        if not selection:
            messagebox.showinfo("Traceroute", "Sélectionnez une adresse IP")
            return
        ip = self.amr_listbox.get(selection[0])

        # Show a progress message
        messagebox.showinfo("Traceroute", f"Lancement du traceroute vers {ip}...\nCela peut prendre quelques secondes.")

        hops = self._perform_traceroute(ip)
        if hops is None:
            messagebox.showerror("Traceroute", f"Echec du traceroute vers {ip}.\nVérifiez :\n• La connectivité réseau\n• L'adresse IP\n• Les permissions système")
        else:
            # Afficher les résultats détaillés dans une nouvelle fenêtre
            self._show_detailed_traceroute_results(ip, hops)

    def _perform_traceroute(self, ip: str) -> Optional[int]:
        try:
            # Use appropriate command based on operating system
            if os.name == 'nt':  # Windows
                # Windows uses tracert command
                result = subprocess.run([
                    "tracert", "-d", ip
                ], capture_output=True, text=True, check=False, timeout=30)
            else:  # Unix-like systems (Linux, macOS)
                # Unix systems use traceroute command
                result = subprocess.run([
                    "traceroute", "-n", ip
                ], capture_output=True, text=True, check=False, timeout=30)

            if result.returncode != 0:
                logging.error(f"Traceroute command failed with return code {result.returncode}")
                return None

            # Parse output to count hops and extract detailed information
            hop_lines = [
                line for line in result.stdout.splitlines()
                if re.match(r"^\s*\d+\s", line)
            ]

            # Store detailed traceroute information
            self.last_traceroute_details = {
                'target_ip': ip,
                'hop_count': len(hop_lines),
                'hops': [],
                'raw_output': result.stdout,
                'execution_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Parse each hop for detailed information
            for hop_line in hop_lines:
                hop_info = self._parse_hop_line(hop_line)
                if hop_info:
                    self.last_traceroute_details['hops'].append(hop_info)

            return len(hop_lines)
        except FileNotFoundError as e:
            logging.error(f"Traceroute command not found: {e}")
            return None
        except subprocess.TimeoutExpired:
            logging.error(f"Traceroute timeout for {ip}")
            return None
        except Exception as e:
            logging.error(f"Traceroute error: {e}")
            return None

    def _parse_hop_line(self, line: str) -> Optional[dict]:
        """Parse une ligne de traceroute pour extraire les informations détaillées"""
        try:
            if os.name == 'nt':  # Windows tracert format
                # Format: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
                # ou     "  1     *        *        *     Request timed out."
                parts = line.strip().split()
                if len(parts) >= 2:
                    hop_num = int(parts[0])

                    if "Request timed out" in line or "*" in line:
                        return {
                            'hop': hop_num,
                            'ip': 'timeout',
                            'times': ['*', '*', '*'],
                            'avg_time': None,
                            'status': 'timeout'
                        }

                    # Chercher l'IP (dernier élément qui ressemble à une IP)
                    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
                    ip_matches = re.findall(ip_pattern, line)
                    ip = ip_matches[-1] if ip_matches else 'unknown'

                    # Extraire les temps de réponse
                    time_pattern = r'(\d+)\s*ms|<(\d+)\s*ms|\*'
                    time_matches = re.findall(r'(\d+)\s*ms|<(\d+)\s*ms|\*', line)
                    times = []
                    numeric_times = []

                    for match in time_matches:
                        if match[0]:  # Temps normal
                            time_val = int(match[0])
                            times.append(f"{time_val} ms")
                            numeric_times.append(time_val)
                        elif match[1]:  # Temps <X ms
                            time_val = int(match[1])
                            times.append(f"<{time_val} ms")
                            numeric_times.append(time_val)
                        else:  # Timeout *
                            times.append("*")

                    avg_time = sum(numeric_times) / len(numeric_times) if numeric_times else None

                    return {
                        'hop': hop_num,
                        'ip': ip,
                        'times': times,
                        'avg_time': avg_time,
                        'status': 'success' if numeric_times else 'partial_timeout'
                    }
            else:  # Unix traceroute format
                # Format similaire mais peut varier selon les systèmes
                parts = line.strip().split()
                if len(parts) >= 2:
                    hop_num = int(parts[0])
                    # Implémentation simplifiée pour Unix
                    return {
                        'hop': hop_num,
                        'ip': parts[1] if len(parts) > 1 else 'unknown',
                        'times': parts[2:] if len(parts) > 2 else [],
                        'avg_time': None,
                        'status': 'success'
                    }

        except (ValueError, IndexError) as e:
            logging.warning(f"Erreur lors du parsing de la ligne traceroute: {line} - {e}")

        return None

    def _show_detailed_traceroute_results(self, ip: str, hop_count: int):
        """Affiche les résultats détaillés du traceroute dans une nouvelle fenêtre"""
        if not hasattr(self, 'last_traceroute_details'):
            messagebox.showinfo("Traceroute", f"Traceroute vers {ip} réussi\n\nNombre de sauts : {hop_count}")
            return

        details = self.last_traceroute_details        # Créer une nouvelle fenêtre pour les détails
        result_window = tk.Toplevel(self.master)
        result_window.title(f"Traceroute vers {ip}")
        result_window.geometry("800x650")
        result_window.resizable(True, True)

        # Frame principal avec padding
        main_frame = ttk.Frame(result_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Titre et informations générales
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(title_frame, text=f"Traceroute vers {ip}",
                 font=('Arial', 14, 'bold')).pack(anchor='w')
        ttk.Label(title_frame, text=f"Exécuté le: {details['execution_time']}",
                 font=('Arial', 10)).pack(anchor='w')
        ttk.Label(title_frame, text=f"Nombre total de sauts: {details['hop_count']}",
                 font=('Arial', 10, 'bold')).pack(anchor='w')

        # Analyse du chemin réseau
        analysis_frame = ttk.LabelFrame(main_frame, text="Analyse du chemin réseau", padding=5)
        analysis_frame.pack(fill=tk.X, pady=(0, 10))

        analysis_text = self._analyze_traceroute_path(details)
        analysis_label = ttk.Label(analysis_frame, text=analysis_text, font=('Arial', 9))
        analysis_label.pack(anchor='w', fill=tk.X)

        # Tableau des sauts avec scrollbar
        table_frame = ttk.LabelFrame(main_frame, text="Détail des sauts", padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Créer un tableau avec Treeview
        columns = ('Saut', 'Adresse IP', 'Temps 1', 'Temps 2', 'Temps 3', 'Moy.', 'Statut')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)

        # Configurer les colonnes
        tree.heading('Saut', text='#')
        tree.heading('Adresse IP', text='Adresse IP')
        tree.heading('Temps 1', text='Temps 1')
        tree.heading('Temps 2', text='Temps 2')
        tree.heading('Temps 3', text='Temps 3')
        tree.heading('Moy.', text='Moyenne')
        tree.heading('Statut', text='Statut')

        tree.column('Saut', width=50, anchor='center')
        tree.column('Adresse IP', width=120, anchor='center')
        tree.column('Temps 1', width=80, anchor='center')
        tree.column('Temps 2', width=80, anchor='center')
        tree.column('Temps 3', width=80, anchor='center')
        tree.column('Moy.', width=80, anchor='center')
        tree.column('Statut', width=100, anchor='center')

        # Remplir le tableau avec les données
        for hop in details['hops']:
            status_display = {
                'success': '✅ OK',
                'timeout': '❌ Timeout',
                'partial_timeout': '⚠️ Partiel'
            }.get(hop.get('status', 'unknown'), '❓ Inconnu')

            # Préparer les temps d'affichage
            times = hop.get('times', ['*', '*', '*'])
            while len(times) < 3:
                times.append('*')

            avg_display = f"{hop['avg_time']:.1f} ms" if hop.get('avg_time') is not None else '*'

            tree.insert('', tk.END, values=(
                hop['hop'],
                hop['ip'],
                times[0],
                times[1] if len(times) > 1 else '*',
                times[2] if len(times) > 2 else '*',
                avg_display,
                status_display
            ))

        # Ajouter scrollbar au tableau
        tree_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Zone de texte brut (repliable)
        raw_frame = ttk.LabelFrame(main_frame, text="Sortie brute (cliquez pour voir/masquer)", padding=5)
        raw_frame.pack(fill=tk.X, pady=(0, 10))

        self.raw_text_visible = False
        raw_text = tk.Text(raw_frame, height=8, wrap=tk.WORD, font=('Courier', 9))
        raw_scroll = ttk.Scrollbar(raw_frame, command=raw_text.yview)
        raw_text.configure(yscrollcommand=raw_scroll.set)
        raw_text.insert('1.0', details['raw_output'])
        raw_text.config(state=tk.DISABLED)

        def toggle_raw_output():
            if self.raw_text_visible:
                raw_text.pack_forget()
                raw_scroll.pack_forget()
                self.raw_text_visible = False
            else:
                raw_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                raw_scroll.pack(side=tk.RIGHT, fill=tk.Y)
                self.raw_text_visible = True

        raw_frame.bind('<Button-1>', lambda e: toggle_raw_output())
        ttk.Label(raw_frame, text="(Cliquez ici pour voir/masquer la sortie complète)").pack()

        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="📋 Copier résultats",
                  command=lambda: self._copy_traceroute_to_clipboard(details)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="💾 Sauvegarder",
                  command=lambda: self._save_traceroute_results(details)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Relancer",
                  command=lambda: [result_window.destroy(), self.traceroute_selected_ip()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Fermer",
                  command=result_window.destroy).pack(side=tk.RIGHT)        # Centrer la fenêtre
        result_window.update_idletasks()
        x = (result_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (result_window.winfo_screenheight() // 2) - (650 // 2)
        result_window.geometry(f"800x650+{x}+{y}")

    def _analyze_traceroute_path(self, details: dict) -> str:
        """Analyse le chemin traceroute et fournit des informations utiles"""
        hops = details.get('hops', [])
        if not hops:
            return "Aucune donnée à analyser."

        analysis = []

        # Analyser les temps de réponse
        successful_hops = [hop for hop in hops if hop.get('avg_time') is not None]
        if successful_hops:
            avg_times = [hop['avg_time'] for hop in successful_hops]
            total_time = max(avg_times) if avg_times else 0

            analysis.append(f"⏱️ Temps total estimé: {total_time:.1f} ms")

            # Identifier les sauts lents
            if avg_times:
                slow_threshold = sum(avg_times) / len(avg_times) * 2  # 2x la moyenne
                slow_hops = [hop for hop in successful_hops if hop['avg_time'] > slow_threshold]
                if slow_hops:
                    analysis.append(f"🐌 Sauts lents détectés: {len(slow_hops)} (>{slow_threshold:.1f}ms)")

        # Analyser les timeouts
        timeout_hops = [hop for hop in hops if hop.get('status') in ['timeout', 'partial_timeout']]
        if timeout_hops:
            analysis.append(f"⚠️ Sauts avec timeouts: {len(timeout_hops)}")

        # Analyser le type de réseau
        first_hop = hops[0] if hops else None
        if first_hop and first_hop.get('ip') != 'timeout':
            ip = first_hop['ip']
            if ip.startswith('192.168.'):
                analysis.append("🏠 Réseau local privé (192.168.x.x)")
            elif ip.startswith('10.'):
                analysis.append("🏢 Réseau d'entreprise privé (10.x.x.x)")
            elif ip.startswith('172.'):
                analysis.append("🏢 Réseau privé (172.x.x.x)")
            else:
                analysis.append("🌐 Connexion directe ou réseau public")

        return " | ".join(analysis) if analysis else "Analyse en cours..."

    def _copy_traceroute_to_clipboard(self, details: dict):
        """Copie les résultats du traceroute dans le presse-papiers"""
        try:
            text = f"Traceroute vers {details['target_ip']}\n"
            text += f"Exécuté le: {details['execution_time']}\n"
            text += f"Nombre de sauts: {details['hop_count']}\n\n"

            text += "Détail des sauts:\n"
            text += "Saut | Adresse IP      | Temps 1   | Temps 2   | Temps 3   | Moyenne   | Statut\n"
            text += "-" * 80 + "\n"

            for hop in details['hops']:
                times = hop.get('times', ['*', '*', '*'])
                while len(times) < 3:
                    times.append('*')

                avg_str = f"{hop['avg_time']:.1f}ms" if hop.get('avg_time') else '*'
                status = hop.get('status', 'unknown')

                text += f"{hop['hop']:4d} | {hop['ip']:15s} | {times[0]:9s} | {times[1]:9s} | {times[2]:9s} | {avg_str:9s} | {status}\n"

            self.master.clipboard_clear()
            self.master.clipboard_append(text)
            messagebox.showinfo("Copié", "Résultats copiés dans le presse-papiers!")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la copie: {str(e)}")

    def _save_traceroute_results(self, details: dict):
        """Sauvegarde les résultats du traceroute dans un fichier"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = f"traceroute_{details['target_ip']}_{timestamp}.txt"

            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
                title="Sauvegarder les résultats du traceroute",
                initialfile=default_filename
            )

            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Traceroute vers {details['target_ip']}\n")
                    f.write(f"Exécuté le: {details['execution_time']}\n")
                    f.write(f"Nombre de sauts: {details['hop_count']}\n\n")

                    f.write("Analyse:\n")
                    f.write(self._analyze_traceroute_path(details) + "\n\n")

                    f.write("Détail des sauts:\n")
                    f.write("=" * 80 + "\n")

                    for hop in details['hops']:
                        f.write(f"Saut {hop['hop']:2d}: {hop['ip']}\n")
                        f.write(f"  Temps: {', '.join(hop.get('times', ['*']))}\n")
                        if hop.get('avg_time'):
                            f.write(f"  Moyenne: {hop['avg_time']:.1f} ms\n")
                        f.write(f"  Statut: {hop.get('status', 'unknown')}\n\n")

                    f.write("\nSortie brute du système:\n")
                    f.write("=" * 80 + "\n")
                    f.write(details['raw_output'])

                messagebox.showinfo("Sauvegardé", f"Résultats sauvegardés dans:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    # === MÉTHODES DE NAVIGATION TEMPORELLE ===

    def toggle_realtime_mode(self):
        """Bascule entre mode temps réel et navigation"""
        self.is_real_time = self.realtime_var.get()

        try:
            if self.is_real_time:
                # Aller à la fin pour afficher les dernières données
                self.go_to_end()
            # Pas besoin d'action spéciale quand on désactive le temps réel
            # La vue reste à la position actuelle
        except Exception as e:
            logging.error(f"Erreur dans toggle_realtime_mode: {str(e)}")
            # Éviter le crash en cas d'erreur

    def go_live(self):
        """Retourne au mode temps réel"""
        self.is_real_time = True
        self.view_mode.set("direct")
        if self.samples:
            self.current_view_start = max(0, len(self.samples) - self.current_view_window)
        self.update_display()
        self.context_label.config(text="📡 Mode direct actif - Suivi en temps réel")

    def go_to_next_alert(self):
        """Va à la prochaine alerte détectée"""
        if not self.samples:
            self.context_label.config(text="❌ Aucune donnée disponible")
            return

        current_pos = self.current_view_start if not self.is_real_time else len(self.samples)

        for i, sample in enumerate(self.samples[current_pos:], current_pos):
            if self._has_alert(sample):
                self.is_real_time = False
                self.view_mode.set("analysis")
                self.current_view_start = max(0, i - 30)  # Centrer sur l'alerte
                self.current_view_window = 60  # 1 minute de contexte
                self.update_display()
                alert_time = self._get_relative_time(i)
                self.context_label.config(text=f"🚨 Alerte trouvée {alert_time}")
                return

        self.context_label.config(text="✅ Aucune alerte trouvée après cette position")

    def go_to_previous_alert(self):
        """Va à l'alerte précédente"""
        if not self.samples:
            self.context_label.config(text="❌ Aucune donnée disponible")
            return

        current_pos = self.current_view_start if not self.is_real_time else len(self.samples)

        # Chercher en arrière
        for i in range(min(current_pos - 1, len(self.samples) - 1), -1, -1):
            if self._has_alert(self.samples[i]):
                self.is_real_time = False
                self.view_mode.set("analysis")
                self.current_view_start = max(0, i - 30)
                self.current_view_window = 60
                self.update_display()
                alert_time = self._get_relative_time(i)
                self.context_label.config(text=f"🚨 Alerte précédente {alert_time}")
                return

        self.context_label.config(text="✅ Aucune alerte trouvée avant cette position")

    def go_to_signal_peak(self):
        """Va au pic de signal le plus élevé"""
        if not self.samples:
            self.context_label.config(text="❌ Aucune donnée disponible")
            return

        signals = [s.signal_strength for s in self.samples]
        peak_idx = signals.index(max(signals))

        self.is_real_time = False
        self.view_mode.set("analysis")
        self.current_view_start = max(0, peak_idx - 30)
        self.current_view_window = 60
        self.update_display()
        peak_time = self._get_relative_time(peak_idx)
        self.context_label.config(text=f"📈 Meilleur signal: {max(signals)} dBm {peak_time}")

    def go_to_signal_low(self):
        """Va au signal le plus faible"""
        if not self.samples:
            self.context_label.config(text="❌ Aucune donnée disponible")
            return

        signals = [s.signal_strength for s in self.samples]
        low_idx = signals.index(min(signals))

        self.is_real_time = False
        self.view_mode.set("analysis")
        self.current_view_start = max(0, low_idx - 30)
        self.current_view_window = 60
        self.update_display()
        low_time = self._get_relative_time(low_idx)
        self.context_label.config(text=f"📉 Signal le plus faible: {min(signals)} dBm {low_time}")

    def change_view_mode(self):
        """Change le mode de visualisation"""
        mode = self.view_mode.get()

        if mode == "direct":
            self.is_real_time = True
            self.go_live()
            self.context_label.config(text="📡 Mode suivi direct - Les données s'affichent en temps réel")
        else:
            self.is_real_time = False
            self.context_label.config(text="📊 Mode analyse - Naviguez avec les boutons ou la souris sur les graphiques")

    def change_temporal_view(self):
        """Change la vue temporelle (1min, 5min, total)"""
        selected = self.temporal_view_var.get()
        self.temporal_view = selected
        
        # Calculer le nombre d'échantillons selon la vue sélectionnée
        # En assumant 1 échantillon par seconde
        if selected == "1min":
            self.current_view_window = 60  # 1 minute = 60 échantillons
        elif selected == "5min":
            self.current_view_window = 300  # 5 minutes = 300 échantillons
        elif selected == "total":
            self.current_view_window = len(self.samples) if self.samples else 300
        
        # Si en mode temps réel, ajuster la position de début
        if self.is_real_time and self.samples:
            self.current_view_start = max(0, len(self.samples) - self.current_view_window)
        
        # Mettre à jour l'affichage
        self.update_display()
        
        # Mettre à jour le label contextuel
        view_labels = {
            "1min": "⏱️ Vue 1 minute - Analyse détaillée",
            "5min": "⏱️ Vue 5 minutes - Analyse standard", 
            "total": "⏱️ Vue totale - Historique complet"
        }
        
        current_label = self.context_label.cget("text")
        # Garder le mode (direct/analyse) mais changer la partie temporelle
        if "Mode suivi direct" in current_label:
            self.context_label.config(text=f"📡 Mode suivi direct - {view_labels[selected]}")
        else:
            self.context_label.config(text=f"📊 Mode analyse - {view_labels[selected]}")

    def open_fullscreen_graphs(self):
        """Ouvre les graphiques en plein écran dans une nouvelle fenêtre"""
        if self.fullscreen_window and self.fullscreen_window.winfo_exists():
            self.fullscreen_window.lift()
            return

        self.fullscreen_window = tk.Toplevel(self.master)
        self.fullscreen_window.title("Graphiques en plein écran")

        # Adapter la taille selon la résolution de l'écran
        screen_width = self.fullscreen_window.winfo_screenwidth()
        screen_height = self.fullscreen_window.winfo_screenheight()

        # Pour les petits écrans, utiliser une fenêtre maximisée mais pas plein écran
        if screen_width < 1366 or screen_height < 768:
            # Utiliser 90% de la taille d'écran pour laisser de la place
            width = int(screen_width * 0.9)
            height = int(screen_height * 0.85)
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.fullscreen_window.geometry(f"{width}x{height}+{x}+{y}")
        else:
            # Sur les grands écrans, utiliser le mode zoomé
            try:
                self.fullscreen_window.state('zoomed')
            except tk.TclError:
                # Fallback si zoomed ne fonctionne pas
                self.fullscreen_window.geometry("1200x800")

        # Créer une nouvelle figure pour le plein écran avec une taille adaptée
        fig_width = max(10, min(16, screen_width / 100))
        fig_height = max(6, min(10, screen_height / 120))
        fs_fig = Figure(figsize=(fig_width, fig_height))
        fs_fig.subplots_adjust(hspace=0.4, left=0.1, right=0.95, top=0.95, bottom=0.15)

        # Signal subplot
        self.fs_ax1 = fs_fig.add_subplot(211)
        self.fs_ax1.set_title("Force du signal WiFi", fontsize=12)
        self.fs_ax1.set_ylabel("Signal (dBm)")
        self.fs_ax1.grid(True, alpha=0.3)
        self.fs_signal_line, = self.fs_ax1.plot([], [], 'b-', linewidth=2, label="Signal")
        # Ne pas fixer les limites ici, elles seront ajustées dynamiquement
        self.fs_ax1.legend()

        # Quality subplot
        self.fs_ax2 = fs_fig.add_subplot(212)
        self.fs_ax2.set_title("Qualité de la connexion", fontsize=12)
        self.fs_ax2.set_ylabel("Qualité (%)")
        self.fs_ax2.set_xlabel("Temps (échantillons)")
        self.fs_ax2.grid(True, alpha=0.3)
        self.fs_quality_line, = self.fs_ax2.plot([], [], 'g-', linewidth=2, label="Qualité")
        # Garder les limites fixes pour la qualité (0-100%)
        self.fs_ax2.set_ylim(0, 100)
        self.fs_ax2.legend()

        # Canvas avec gestion des barres de défilement pour petits écrans
        canvas_frame = ttk.Frame(self.fullscreen_window)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.fs_canvas = FigureCanvasTkAgg(fs_fig, master=canvas_frame)
        self.fs_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Toolbar de navigation
        fs_toolbar = NavigationToolbar2Tk(self.fs_canvas, canvas_frame)
        fs_toolbar.update()

        # Frame pour les boutons en bas
        button_frame = ttk.Frame(self.fullscreen_window)
        button_frame.pack(pady=5)

        # Bouton pour synchroniser la vue
        ttk.Button(button_frame, text="Synchroniser vue",
                  command=self.sync_fullscreen_view).pack(side=tk.LEFT, padx=5)        # Bouton pour fermer
        ttk.Button(button_frame, text="Fermer",
                  command=self.fullscreen_window.destroy).pack(side=tk.LEFT, padx=5)

        # Mettre à jour les graphiques avec la vue actuelle
        self.update_fullscreen_display()

    def update_fullscreen_display(self):
        """Met à jour les graphiques en plein écran avec la même vue que l'écran principal"""
        if not hasattr(self, 'fullscreen_window') or not self.fullscreen_window or not self.fullscreen_window.winfo_exists():
            return

        if not self.samples:
            return

        try:
            # Utiliser exactement la même logique que la vue principale
            samples_snapshot = list(self.samples)

            # Ajuster current_view_window pour la vue "total" (même logique que update_display)
            if self.temporal_view == "total":
                self.current_view_window = len(samples_snapshot) if samples_snapshot else 300

            # Déterminer la plage d'affichage selon le mode (même logique que update_display)
            if self.is_real_time:
                start_idx = max(0, len(samples_snapshot) - self.current_view_window)
                end_idx = len(samples_snapshot)
            else:
                start_idx = self.current_view_start
                end_idx = min(len(samples_snapshot), start_idx + self.current_view_window)

                # Si on essaie d'afficher plus d'échantillons qu'il n'y en a,
                # ajuster le début pour montrer les derniers échantillons disponibles
                if end_idx - start_idx < self.current_view_window and end_idx == len(samples_snapshot):
                    start_idx = max(0, end_idx - self.current_view_window)

            # Extraire les données à afficher (même vue que l'écran principal)
            display_samples = samples_snapshot[start_idx:end_idx]
            if not display_samples:
                return

            signals = [s.signal_strength for s in display_samples]
            qualities = [s.quality for s in display_samples]
            x_data = range(len(signals))

            # Mettre à jour les données
            if hasattr(self, 'fs_signal_line') and self.fs_signal_line is not None:
                self.fs_signal_line.set_data(x_data, signals)

                # Ajuster automatiquement les axes Y pour le signal
                if signals and hasattr(self, 'fs_ax1'):
                    min_signal = min(signals)
                    max_signal = max(signals)
                    # Ajouter une marge de 5 dBm de chaque côté
                    margin = 5
                    self.fs_ax1.set_ylim(min_signal - margin, max_signal + margin)
                    # Ajuster l'axe X
                    if len(x_data) > 0:
                        self.fs_ax1.set_xlim(0, max(x_data) if x_data else 1)

            if hasattr(self, 'fs_quality_line') and self.fs_quality_line is not None:
                self.fs_quality_line.set_data(x_data, qualities)

                # Ajuster l'axe X pour la qualité aussi
                if hasattr(self, 'fs_ax2') and len(x_data) > 0:
                    self.fs_ax2.set_xlim(0, max(x_data) if x_data else 1)

            # Redessiner
            if hasattr(self, 'fs_canvas') and self.fs_canvas is not None:
                self.fs_canvas.draw_idle()

        except Exception as e:
            logging.error(f"Erreur dans update_fullscreen_display: {str(e)}")

    def sync_fullscreen_view(self):
        """Synchronise manuellement la vue plein écran avec la vue principale"""
        self.update_fullscreen_display()

    def go_to_start(self):
        """Va au début des données"""
        try:
            self.is_real_time = False
            self.view_mode.set("analysis")
            self.current_view_start = 0
            self.current_view_window = 60  # Vue d'une minute
            self.update_display()
            self.context_label.config(text="📊 Début de l'analyse - Premières données collectées")
        except Exception as e:
            logging.error(f"Erreur dans go_to_start: {str(e)}")

    def show_instructions_guide(self):
        """Affiche le guide des instructions personnalisées OpenAI dans une nouvelle fenêtre"""
        import os

        guide_window = tk.Toplevel(self.master)
        guide_window.title("Guide des Instructions Personnalisées OpenAI")
        guide_window.geometry("800x600")
        guide_window.resizable(True, True)

        # Créer un frame avec scrollbar
        main_frame = ttk.Frame(guide_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Zone de texte avec scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        guide_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=('Arial', 10),
            relief=tk.FLAT,
            bg='white',
            fg='black'
        )

        scrollbar = ttk.Scrollbar(text_frame, command=guide_text.yview)
        guide_text.configure(yscrollcommand=scrollbar.set)

        guide_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Lire et afficher le contenu du guide
        try:
            guide_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OPENAI_CUSTOM_INSTRUCTIONS_GUIDE.md')

            if os.path.exists(guide_path):
                with open(guide_path, 'r', encoding='utf-8') as f:
                    guide_content = f.read()

                # Configurer les styles pour le markdown simple
                guide_text.tag_configure("title", font=('Arial', 14, 'bold'), foreground='navy')
                guide_text.tag_configure("subtitle", font=('Arial', 12, 'bold'), foreground='darkblue')
                guide_text.tag_configure("code", font=('Courier', 10), background='lightgray', foreground='darkgreen')
                guide_text.tag_configure("bold", font=('Arial', 10, 'bold'))
                guide_text.tag_configure("normal", font=('Arial', 10))

                # Parser et afficher le contenu avec formatage basique
                self.parse_and_display_markdown(guide_text, guide_content)

            else:
                guide_text.insert('1.0', "❌ Fichier guide non trouvé.\n\n")
                guide_text.insert('end', "Le fichier OPENAI_CUSTOM_INSTRUCTIONS_GUIDE.md devrait se trouver dans le répertoire de l'application.")

        except Exception as e:
            guide_text.insert('1.0', f"❌ Erreur lors du chargement du guide: {str(e)}\n\n")
            guide_text.insert('end', "Vérifiez que le fichier OPENAI_CUSTOM_INSTRUCTIONS_GUIDE.md existe et est accessible.")

        # Rendre le texte en lecture seule
        guide_text.config(state=tk.DISABLED)

        # Bouton de fermeture
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Fermer",
            command=guide_window.destroy
        ).pack(side=tk.RIGHT)

        # Centrer la fenêtre
        guide_window.update_idletasks()
        x = (guide_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (guide_window.winfo_screenheight() // 2) - (600 // 2)
        guide_window.geometry(f"800x600+{x}+{y}")

    def parse_and_display_markdown(self, text_widget, content):
        """Parse le contenu markdown et l'affiche avec formatage basique"""
        lines = content.split('\n')

        for line in lines:
            if line.startswith('# '):
                # Titre principal
                text_widget.insert('end', line[2:] + '\n', "title")
            elif line.startswith('## '):
                # Sous-titre
                text_widget.insert('end', '\n' + line[3:] + '\n', "subtitle")
            elif line.startswith('### '):
                # Sous-sous-titre
                text_widget.insert('end', '\n' + line[4:] + '\n', "bold")
            elif line.startswith('```'):
                # Code block - on l'ignore pour simplifier
                continue
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                # Liste à puces
                text_widget.insert('end', '  • ' + line.strip()[2:] + '\n', "normal")
            elif '**' in line:
                # Texte en gras
                parts = line.split('**')
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Partie entre **
                        text_widget.insert('end', part, "bold")
                    else:
                        text_widget.insert('end', part, "normal")
                text_widget.insert('end', '\n')
            elif line.strip():
                # Ligne normale
                text_widget.insert('end', line + '\n', "normal")
            else:
                # Ligne vide
                text_widget.insert('end', '\n')

    # === MÉTHODES UTILITAIRES MANQUANTES ===

    def _get_relative_time(self, position: int) -> str:
        """Retourne une description du temps relatif pour une position donnée"""
        if not self.samples or position >= len(self.samples):
            return "Position inconnue"        # Calculer le temps relatif en secondes (basé sur l'intervalle de collecte)
        time_offset = position * (self.update_interval / 1000.0)  # Convertir ms en secondes

        if time_offset < 60:
            return f"{int(time_offset)}s"
        elif time_offset < 3600:
            minutes = int(time_offset / 60)
            seconds = int(time_offset % 60)
            return f"{minutes}m{seconds}s" if seconds > 0 else f"{minutes}m"
        else:
            hours = int(time_offset / 3600)
            minutes = int((time_offset % 3600) / 60)
            return f"{hours}h{minutes}m" if minutes > 0 else f"{hours}h"

    def _has_alert(self, sample: WifiSample) -> bool:
        """Vérifie si un échantillon a des alertes selon les seuils configurés"""
        # Signal critiques
        if sample.signal_strength < -85:
            return True
        # Qualité critique
        if sample.quality < 20:
            return True
        # Vérifier les alertes de débit
        if self._check_rate_alerts(sample):
            return True
        return False

    def _check_rate_alerts(self, sample: WifiSample) -> bool:
        """Vérifie s'il y a des problèmes de débit dans l'échantillon"""
        try:
            tx_rate = int(sample.raw_data.get('TransmitRate', '0 Mbps').split()[0])
            rx_rate = int(sample.raw_data.get('ReceiveRate', '0 Mbps').split()[0])

            # Seuils critiques pour les débits
            min_tx_critical = 10  # TX critique si < 10 Mbps
            min_rx_critical = 2   # RX critique si < 2 Mbps
              # Alerte si les deux débits sont vraiment problématiques
            return tx_rate < min_tx_critical and rx_rate < min_rx_critical

        except (ValueError, IndexError, KeyError):
            return False

    def update_amr_status(self, status_data):
        """Met à jour le statut AMR dans l'interface"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_text = f"[{timestamp}] {status_data}\n"
            self.amr_status_text.insert('1.0', status_text)
        except Exception as e:
            logging.error(f"Erreur dans update_amr_status: {e}")

    def open_mac_tag_manager(self):
        """Ouvre la fenêtre de gestion des tags MAC"""
        if self.mac_manager_window and self.mac_manager_window.winfo_exists():
            self.mac_manager_window.lift()
            return

        self.mac_manager_window = tk.Toplevel(self.master)
        self.mac_manager_window.title("Gestion des Tags MAC")
        self.mac_manager_window.geometry("400x500")

        # Frame principal
        main_frame = ttk.Frame(self.mac_manager_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Liste des MAC et leurs tags
        list_frame = ttk.LabelFrame(main_frame, text="MACs et Tags", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.mac_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.mac_listbox.yview)
        self.mac_listbox.configure(yscrollcommand=scrollbar.set)
        self.mac_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Frame pour l'ajout/édition
        edit_frame = ttk.Frame(main_frame)
        edit_frame.pack(fill=tk.X, pady=10)

        ttk.Label(edit_frame, text="MAC:").pack(side=tk.LEFT)
        self.mac_entry = ttk.Entry(edit_frame)
        self.mac_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(edit_frame, text="Tag:").pack(side=tk.LEFT)
        self.tag_entry = ttk.Entry(edit_frame)
        self.tag_entry.pack(side=tk.LEFT, padx=5)

        # Boutons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Ajouter/Modifier",
                  command=self._add_or_update_mac_tag).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer",
                  command=self._delete_mac_tag).pack(side=tk.LEFT, padx=5)        # Remplir la liste
        self._update_mac_list()

        # Gestionnaire d'événements pour la sélection
        self.mac_listbox.bind('<<ListboxSelect>>', self._on_mac_select)

    def _update_mac_list(self):
        """Met à jour la liste des MACs dans l'interface"""
        if hasattr(self, 'mac_listbox'):
            self.mac_listbox.delete(0, tk.END)
            for mac, tag in self.mac_manager.get_all_tags().items():
                self.mac_listbox.insert(tk.END, f"{mac} - {tag}")

    def _add_or_update_mac_tag(self):
        """Ajoute ou met à jour un tag MAC"""
        mac = self.mac_entry.get().strip()
        tag = self.tag_entry.get().strip()
        if mac and tag:
            self.mac_manager.add_tag(mac, tag)
            self._update_mac_list()
            self.mac_entry.delete(0, tk.END)
            self.tag_entry.delete(0, tk.END)

    def _delete_mac_tag(self):
        """Supprime un tag MAC"""
        selection = self.mac_listbox.curselection()
        if selection:
            mac = self.mac_listbox.get(selection[0]).split(" - ")[0]
            self.mac_manager.remove_tag(mac)
            self._update_mac_list()

    def _on_mac_select(self, event):
        """Gère la sélection d'un MAC dans la liste"""
        selection = self.mac_listbox.curselection()
        if selection:
            mac, tag = self.mac_listbox.get(selection[0]).split(" - ")
            self.mac_entry.delete(0, tk.END)
            self.mac_entry.insert(0, mac)
            self.tag_entry.delete(0, tk.END)
            self.tag_entry.insert(0, tag)

    def update_advanced_wifi_stats(self):
        """Met à jour les statistiques WiFi avancées"""
        try:
            if not self.wifi_history_entries:
                # Afficher un message si aucune donnée
                if hasattr(self, 'wifi_advanced_stats_text'):
                    self.wifi_advanced_stats_text.delete('1.0', tk.END)
                    self.wifi_advanced_stats_text.insert('1.0', "=== Statistiques WiFi Avancées ===\n\nAucune donnée disponible.\nDémarrez la collecte pour voir les statistiques.")
                return            # Calculer les statistiques sur les dernières entrées
            recent_entries = self.wifi_history_entries[-300:]  # 300 dernières entrées

            # Compter les alertes
            total_samples = len(recent_entries)
            samples_with_alerts = sum(1 for entry in recent_entries if entry['alerts'])
            alert_percentage = (samples_with_alerts / total_samples * 100) if total_samples > 0 else 0

            # Calculer les moyennes
            avg_signal = sum(entry['signal'] for entry in recent_entries) / len(recent_entries)
            avg_quality = sum(entry['quality'] for entry in recent_entries) / len(recent_entries)            # Calculer min/max
            signals = [entry['signal'] for entry in recent_entries]
            qualities = [entry['quality'] for entry in recent_entries]
            min_signal, max_signal = min(signals), max(signals)
            min_quality, max_quality = min(qualities), max(qualities)

            # Compter les différents types d'alertes
            alert_types = {}
            for entry in recent_entries:
                for alert in entry['alerts']:
                    alert_type = alert.split(':')[0] if ':' in alert else alert[:20]
                    alert_types[alert_type] = alert_types.get(alert_type, 0) + 1

            # Analyser les BSSID (adresses MAC des points d'accès)
            bssid_info = {}
            for entry in recent_entries:
                bssid = entry.get('bssid', 'Unknown')
                if bssid and bssid != 'Unknown':
                    if bssid not in bssid_info:
                        bssid_info[bssid] = {
                            'count': 0,
                            'signals': [],
                            'qualities': [],
                            'alerts': 0
                        }
                    bssid_info[bssid]['count'] += 1
                    bssid_info[bssid]['signals'].append(entry['signal'])
                    bssid_info[bssid]['qualities'].append(entry['quality'])
                    if entry['alerts']:
                        bssid_info[bssid]['alerts'] += 1            # Évaluation de la stabilité
            signal_stability = "Excellent" if max_signal - min_signal < 10 else "Bon" if max_signal - min_signal < 20 else "Variable"

            # Formatage des statistiques pour l'affichage
            stats_text = "=== STATISTIQUES WiFi AVANCÉES ===\n"
            stats_text += f"Période d'analyse : {len(recent_entries)} échantillons\n\n"

            stats_text += "📶 SIGNAL :\n"
            stats_text += f"• Moyenne : {avg_signal:.1f} dBm\n"
            stats_text += f"• Min/Max : {min_signal:.1f} / {max_signal:.1f} dBm\n"
            stats_text += f"• Variation : {max_signal - min_signal:.1f} dB\n"
            stats_text += f"• Stabilité : {signal_stability}\n\n"

            stats_text += "📊 QUALITÉ :\n"
            stats_text += f"• Moyenne : {avg_quality:.1f}%\n"
            stats_text += f"• Min/Max : {min_quality:.1f} / {max_quality:.1f}%\n"
            stats_text += f"• Variation : {max_quality - min_quality:.1f}%\n\n"

            stats_text += "🚨 ALERTES :\n"
            stats_text += f"• Pourcentage d'échantillons avec alertes : {alert_percentage:.1f}%\n"
            stats_text += f"• Échantillons avec alertes : {samples_with_alerts}/{total_samples}\n"

            if alert_types:
                stats_text += "• Types d'alertes détectées :\n"
                for alert_type, count in sorted(alert_types.items(), key=lambda x: x[1], reverse=True):
                    stats_text += f"  - {alert_type} : {count} fois\n"
            else:
                stats_text += "• Aucune alerte détectée\n"

            # Section BSSID/MAC des points d'accès
            stats_text += "\n📡 POINTS D'ACCÈS (BSSID/MAC) :\n"
            if bssid_info:
                stats_text += f"• Nombre de points d'accès détectés : {len(bssid_info)}\n"

                # Trier par nombre d'occurrences (le plus utilisé en premier)
                sorted_bssids = sorted(bssid_info.items(), key=lambda x: x[1]['count'], reverse=True)

                for bssid, info in sorted_bssids[:5]:  # Afficher les 5 premiers
                    avg_signal = sum(info['signals']) / len(info['signals'])
                    avg_quality = sum(info['qualities']) / len(info['qualities'])
                    alert_rate = (info['alerts'] / info['count'] * 100) if info['count'] > 0 else 0

                    tag = self.mac_manager.get_tag(bssid)
                    tag_str = f" ({tag})" if tag else ""
                    stats_text += f"\n  🔸 {bssid}{tag_str}\n"
                    stats_text += f"    • Échantillons : {info['count']}\n"
                    stats_text += f"    • Signal moyen : {avg_signal:.1f} dBm\n"
                    stats_text += f"    • Qualité moyenne : {avg_quality:.1f}%\n"
                    stats_text += f"    • Taux d'alertes : {alert_rate:.1f}%\n"

                if len(bssid_info) > 5:
                    stats_text += f"\n  ... et {len(bssid_info) - 5} autres points d'accès\n"
            else:
                stats_text += "• Aucune adresse MAC disponible dans les données\n"

            stats_text += "\n💡 ÉVALUATION GLOBALE :\n"

            # Évaluation de la performance globale
            if avg_signal > -60 and avg_quality > 80 and alert_percentage < 10:
                evaluation = "🟢 EXCELLENT - Réseau optimal pour les AMR"
            elif avg_signal > -70 and avg_quality > 60 and alert_percentage < 25:
                evaluation = "🟡 BON - Réseau acceptable avec surveillance"
            else:
                evaluation = "🔴 ATTENTION - Réseau nécessitant des améliorations"

            stats_text += f"• {evaluation}\n"

            # Recommandations IT
            stats_text += "\n🔧 INFORMATIONS IT :\n"
            if avg_signal < -70:
                stats_text += "• Signal faible : Vérifier couverture AP ou position antennes\n"
            if max_signal - min_signal > 20:
                stats_text += "• Signal instable : Contrôler interférences ou handover\n"
            if alert_percentage > 20:
                stats_text += "• Nombreuses alertes : Analyser logs réseau détaillés\n"
            if avg_quality < 60:
                stats_text += "• Qualité faible : Vérifier config QoS et bande passante\n"

            # Mettre à jour l'interface
            if hasattr(self, 'wifi_advanced_stats_text'):
                self.wifi_advanced_stats_text.delete('1.0', tk.END)
                self.wifi_advanced_stats_text.insert('1.0', stats_text)

        except Exception as e:
            logging.error(f"Erreur dans update_advanced_wifi_stats: {str(e)}")
            if hasattr(self, 'wifi_advanced_stats_text'):
                self.wifi_advanced_stats_text.delete('1.0', tk.END)
                self.wifi_advanced_stats_text.insert('1.0', f"Erreur lors du calcul des statistiques :\n{str(e)}")


def main():
    """Point d'entrée principal de l'application"""
    try:
        # Configuration de base du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('wifi_analyzer.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        logging.info("🚀 Démarrage de l'application WiFi Analyzer")

        # Créer l'interface principale
        root = tk.Tk()
        app = NetworkAnalyzerUI(root)

        # Lancer l'application
        logging.info("✅ Interface créée, lancement de la boucle principale")
        root.mainloop()

    except Exception as e:
        error_msg = f"❌ Erreur fatale lors du lancement: {str(e)}"
        logging.error(error_msg)
        print(error_msg)

        # Afficher l'erreur à l'utilisateur
        import traceback
        traceback.print_exc()

        # Essayer d'afficher une boîte de dialogue d'erreur
        try:
            messagebox.showerror("Erreur de lancement", f"Impossible de démarrer l'application:\n\n{str(e)}")
        except:
            pass

        return False

    return True


if __name__ == "__main__":
    print("🎯 WIFI ANALYZER - APPLICATION PRINCIPALE")
    print("=" * 50)
    success = main()
    if not success:
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)
