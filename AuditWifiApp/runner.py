# -*- coding: utf-8 -*-
import sys
import json
import logging
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

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
from dotenv import load_dotenv

# Charger automatiquement les variables d'environnement depuis un fichier .env
load_dotenv()

from network_analyzer import NetworkAnalyzer
from amr_monitor import AMRMonitor
from wifi.wifi_collector import WifiSample
from src.ai.simple_moxa_analyzer import analyze_moxa_logs
from config_manager import ConfigurationManager

class NetworkAnalyzerUI:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("Analyseur Réseau WiFi & Moxa")
        self.master.state('zoomed')        # Initialisation des composants
        self.analyzer = NetworkAnalyzer()
        self.samples: List[WifiSample] = []
        self.amr_ips: List[str] = []
        self.amr_monitor: Optional[AMRMonitor] = None

        # Variables pour la navigation temporelle
        self.current_view_start = 0
        self.current_view_window = 100  # Nombre d'échantillons à afficher
        self.is_real_time = True  # Mode temps réel vs navigation
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

        # Configuration du style
        self.setup_style()

        # Création de l'interface
        self.create_interface()

        # Configuration des graphiques
        self.setup_graphs()        # Variables pour les mises à jour
        self.update_interval = 1000  # ms
        self.max_samples = 100

        # Historique pour l'onglet WiFi
        self.wifi_history_entries = []
        self.max_history_entries = 1000

    def setup_style(self):
        """Configure le style de l'interface"""
        style = ttk.Style()
        style.configure("Title.TLabel", font=('Helvetica', 14, 'bold'))
        style.configure("Alert.TLabel", foreground='red', font=('Helvetica', 12))
        style.configure("Stats.TLabel", font=('Helvetica', 10))

        # Style pour le bouton d'analyse
        style.configure("Analyze.TButton",
                       font=('Helvetica', 12),
                       padding=10)

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
        self.stop_button.pack(fill=tk.X, pady=5)        # Zone de statistiques - Compacte
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
        ttk.Button(config_btn_frame, text="Éditer config", command=self.edit_config).pack(side=tk.LEFT, padx=5)

        # Zone d'instructions personnalisées - Compacte
        instr_frame = ttk.LabelFrame(
            self.moxa_frame,
            text="Instructions personnalisées (optionnel) :",
            padding=10,
        )
        instr_frame.pack(fill=tk.X, expand=False, padx=10, pady=(2, 2))

        self.custom_instr_text = tk.Text(instr_frame, height=3, wrap=tk.WORD)
        instr_scroll = ttk.Scrollbar(instr_frame, command=self.custom_instr_text.yview)
        self.custom_instr_text.configure(yscrollcommand=instr_scroll.set)
        self.custom_instr_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        instr_scroll.pack(side=tk.RIGHT, fill=tk.Y)        # Bouton d'analyse
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

        self.amr_listbox = tk.Listbox(amr_control, height=6)
        self.amr_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        self.amr_start_button = ttk.Button(amr_control, text="▶ Démarrer", command=self.start_amr_monitoring)
        self.amr_start_button.pack(fill=tk.X, pady=2)
        self.amr_stop_button = ttk.Button(amr_control, text="⏹ Arrêter", command=self.stop_amr_monitoring, state=tk.DISABLED)
        self.amr_stop_button.pack(fill=tk.X, pady=2)

        status_frame = ttk.LabelFrame(self.amr_frame, text="Statut", padding=10)
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.amr_status_text = tk.Text(status_frame, height=10, wrap=tk.WORD)
        status_scroll = ttk.Scrollbar(status_frame, command=self.amr_status_text.yview)
        self.amr_status_text.configure(yscrollcommand=status_scroll.set)
        self.amr_status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_graphs(self):
        """Configure les graphiques avec navigation temporelle et plein écran"""
        # Variables de navigation
        self.max_samples = 100  # Nb échantillons visibles
        self.current_view_start = 0
        self.current_view_window = 100
        self.is_real_time = True
        self.alert_markers = []

        # Frame principal pour les graphiques
        graph_main_frame = ttk.Frame(self.wifi_frame)
        graph_main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # === CONTRÔLES DE NAVIGATION ===
        nav_frame = ttk.LabelFrame(graph_main_frame, text="🎛️ Navigation Temporelle", padding=5)
        nav_frame.pack(fill=tk.X, pady=(0, 5))

        # Première ligne : boutons principaux
        nav_buttons_frame = ttk.Frame(nav_frame)
        nav_buttons_frame.pack(fill=tk.X, pady=2)

        # Bouton plein écran
        self.fullscreen_button = ttk.Button(
            nav_buttons_frame,
            text="🖥️ Plein Écran",
            command=self.open_fullscreen_graphs
        )
        self.fullscreen_button.pack(side=tk.LEFT, padx=2)

        # Mode temps réel
        self.realtime_var = tk.BooleanVar(value=True)
        self.realtime_check = ttk.Checkbutton(
            nav_buttons_frame,
            text="⏱️ Temps réel",
            variable=self.realtime_var,
            command=self.toggle_realtime_mode
        )
        self.realtime_check.pack(side=tk.LEFT, padx=10)

        # Boutons de navigation
        nav_controls = ttk.Frame(nav_buttons_frame)
        nav_controls.pack(side=tk.RIGHT)

        # Bouton pour activer/désactiver le mode déplacement (pan) sur les graphiques
        self.is_pan_mode = False
        self.pan_button = ttk.Button(nav_controls, text="🖱️", command=self.toggle_pan_mode, width=3)
        self.pan_button.pack(side=tk.LEFT, padx=1)

        ttk.Button(nav_controls, text="⏮️", command=self.go_to_start, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(nav_controls, text="⏪", command=self.go_previous, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(nav_controls, text="⏸️", command=self.pause_navigation, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(nav_controls, text="⏩", command=self.go_next, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(nav_controls, text="⏭️", command=self.go_to_end, width=3).pack(side=tk.LEFT, padx=1)

        # Deuxième ligne : slider temporel et zoom
        slider_frame = ttk.Frame(nav_frame)
        slider_frame.pack(fill=tk.X, pady=2)

        ttk.Label(slider_frame, text="Position:").pack(side=tk.LEFT)
        self.time_slider = ttk.Scale(
            slider_frame,
            from_=0, to=100,
            orient=tk.HORIZONTAL,
            command=self.on_slider_change
        )
        self.time_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Contrôles de zoom
        zoom_frame = ttk.Frame(slider_frame)
        zoom_frame.pack(side=tk.RIGHT)

        ttk.Label(zoom_frame, text="Fenêtre:").pack(side=tk.LEFT)
        self.window_var = tk.StringVar(value="100")
        window_combo = ttk.Combobox(
            zoom_frame,
            textvariable=self.window_var,
            values=["50", "100", "200", "500", "1000", "Tout"],
            width=8,
            state="readonly"
        )
        window_combo.pack(side=tk.LEFT, padx=2)
        window_combo.bind('<<ComboboxSelected>>', self.on_window_change)

        # Info de position
        self.position_label = ttk.Label(nav_frame, text="Position: 0/0 échantillons")
        self.position_label.pack()

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
        self.ax2.set_xlabel("Échantillons")
        self.ax2.grid(True, alpha=0.3)
        self.quality_line, = self.ax2.plot([], [], 'g-', linewidth=2, label="Qualité")
        self.ax2.set_ylim(0, 100)
        self.ax2.legend()

        # Canvas Matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Toolbar de navigation matplotlib
        toolbar_frame = ttk.Frame(graph_main_frame)
        toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Raccourcis clavier pour la navigation

        self.master.bind('<Left>', self.on_left_key)
        self.master.bind('<Right>', self.on_right_key)
        self.master.bind('<Home>', self.on_home_key)
        self.master.bind('<End>', self.on_end_key)
        self.master.bind('<space>', self.on_space_key)


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

    def update_data(self):
        """Met à jour les données en temps réel"""
        if not self.analyzer.is_collecting:
            return

        sample = self.analyzer.wifi_collector.collect_sample()
        if sample:
            self.samples.append(sample)
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

        # Mise à jour onglet Alertes
        if alerts:
            msg = f"Position au {timestamp} :\n"
            msg += "\n".join(alerts)
            self.wifi_alert_text.delete('1.0', tk.END)
            self.wifi_alert_text.insert('1.0', msg)        # Ajouter à l'historique (même si pas d'alertes)
        self.add_to_wifi_history(sample, alerts, timestamp)        # Mettre à jour les stats avancées
        self.update_advanced_wifi_stats()

    def update_display(self):
        """Met à jour les graphiques avec navigation temporelle"""
        if not self.samples:
            return

        try:
            # Créer une copie locale des échantillons pour éviter les problèmes
            # de concurrence lorsque la liste est modifiée pendant la navigation
            samples_snapshot = list(self.samples)

            # Déterminer la plage d'affichage selon le mode
            if self.is_real_time:
                # Mode temps réel : afficher les derniers échantillons
                start_idx = max(0, len(samples_snapshot) - self.current_view_window)
                end_idx = len(samples_snapshot)
            else:
                # Mode navigation : afficher la fenêtre sélectionnée
                start_idx = self.current_view_start
                end_idx = min(len(samples_snapshot), start_idx + self.current_view_window)

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
            self.update_position_info()

        except Exception as e:
            logging.error(f"Erreur générale dans update_display: {e}")
            # Continuer sans faire crasher l'application

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
            return

        # Calcul des statistiques
        current_sample = self.samples[-1]  # Dernier échantillon
        signal_values = [s.signal_strength for s in self.samples[-20:]]  # 20 derniers échantillons
        quality_values = [s.quality for s in self.samples[-20:]]

        # Stats WiFi actuelles
        stats_text = "=== État Actuel ===\n"
        stats_text += f"Signal : {current_sample.signal_strength} dBm\n"
        stats_text += f"Qualité: {current_sample.quality}%\n"

        # Stats moyennes (20 derniers échantillons)
        avg_signal = sum(signal_values) / len(signal_values)
        avg_quality = sum(quality_values) / len(quality_values)
        stats_text += "\n=== Moyenne (20 éch.) ===\n"
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
        self.amr_ip_var.set("")

    def start_amr_monitoring(self) -> None:
        if not self.amr_ips:
            messagebox.showwarning("Monitoring AMR", "Ajoutez au moins une adresse IP")
            return
        self.amr_monitor = AMRMonitor(self.amr_ips, interval=3)
        def amr_callback(res):
            self.master.after(0, self._update_amr_status, res)
        self.amr_monitor.start(amr_callback)
        self.amr_start_button.config(state=tk.DISABLED)
        self.amr_stop_button.config(state=tk.NORMAL)

    def stop_amr_monitoring(self) -> None:
        if self.amr_monitor:
            self.amr_monitor.stop()
            self.amr_monitor = None
        self.amr_start_button.config(state=tk.NORMAL)
        self.amr_stop_button.config(state=tk.DISABLED)

    def _update_amr_status(self, results: Dict[str, Dict[str, Optional[int]]]) -> None:
        lines = []
        for ip, data in results.items():
            if data["reachable"]:
                latency = data["latency"] if data["latency"] is not None else "n/a"
                lines.append(f"{ip} : ✅ {latency} ms")
            else:
                lines.append(f"{ip} : ❌")
        self.amr_status_text.delete("1.0", tk.END)
        self.amr_status_text.insert("1.0", "\n".join(lines))

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

    def on_slider_change(self, value):
        """Gère le changement de position du slider"""
        if self.slider_update_in_progress:
            return

        if not self.is_real_time and self.samples:
            total_samples = len(self.samples)
            position = int(float(value) * total_samples / 100)
            self.current_view_start = max(0, position - self.current_view_window // 2)
            self.update_display()
            self.update_position_info()

    def on_window_change(self, event=None):
        """Gère le changement de taille de fenêtre"""
        window_size = self.window_var.get()
        if window_size == "Tout":
            self.current_view_window = len(self.samples) if self.samples else 100
        else:
            self.current_view_window = int(window_size)

        if not self.is_real_time:
            self.update_display()
            self.update_position_info()

    def go_to_start(self):
        """Va au début des données"""
        try:
            self.is_real_time = False
            self.realtime_var.set(False)
            self.current_view_start = 0
            self.update_display()
            self.update_position_info()
        except Exception as e:
            logging.error(f"Erreur dans go_to_start: {str(e)}")
            # Éviter le crash en cas d'erreur

    def go_to_end(self):
        """Va à la fin des données"""
        try:
            if self.samples:
                self.current_view_start = max(0, len(self.samples) - self.current_view_window)
            self.update_display()
            self.update_position_info()
        except Exception as e:
            logging.error(f"Erreur dans go_to_end: {str(e)}")
            # Éviter le crash en cas d'erreur

    def go_previous(self):
        """Recule dans le temps"""
        try:
            self.is_real_time = False
            self.realtime_var.set(False)
            step = max(1, self.current_view_window // 4)
            self.current_view_start = max(0, self.current_view_start - step)
            self.update_display()
            self.update_position_info()
        except Exception as e:
            logging.error(f"Erreur dans go_previous: {str(e)}")
            # Éviter le crash en cas d'erreur

    def go_next(self):
        """Avance dans le temps"""
        try:
            self.is_real_time = False
            self.realtime_var.set(False)
            if self.samples:
                step = max(1, self.current_view_window // 4)
                max_start = max(0, len(self.samples) - self.current_view_window)
                self.current_view_start = min(max_start, self.current_view_start + step)
            self.update_display()
            self.update_position_info()
        except Exception as e:
            logging.error(f"Erreur dans go_next: {str(e)}")
            # Éviter le crash en cas d'erreur

    def pause_navigation(self):
        """Met en pause/reprend la navigation automatique"""
        try:
            self.is_real_time = not self.is_real_time
            self.realtime_var.set(self.is_real_time)
        except Exception as e:
            logging.error(f"Erreur dans pause_navigation: {str(e)}")
            # Éviter le crash en cas d'erreur


    # Handlers pour les raccourcis clavier
    def on_left_key(self, event=None):
        """Déclenche le déplacement vers la gauche"""
        self.go_previous()

    def on_right_key(self, event=None):
        """Déclenche le déplacement vers la droite"""
        self.go_next()

    def on_home_key(self, event=None):
        """Va au début des données"""
        self.go_to_start()

    def on_end_key(self, event=None):
        """Va à la fin des données"""
        self.go_to_end()

    def on_space_key(self, event=None):
        """Met en pause ou reprend la navigation"""
        self.pause_navigation()


    def toggle_pan_mode(self):
        """Active ou désactive le mode déplacement sur les graphiques"""
        try:
            self.is_pan_mode = not self.is_pan_mode
            # Activer/désactiver sur les toolbars
            if hasattr(self, 'toolbar'):
                self.toolbar.pan()
            if hasattr(self, 'toolbar_fs'):
                self.toolbar_fs.pan()
            # Mettre à jour l'état visuel des boutons
            self.pan_button.config(relief=tk.SUNKEN if self.is_pan_mode else tk.RAISED)
            if hasattr(self, 'pan_button_fs'):
                self.pan_button_fs.config(relief=tk.SUNKEN if self.is_pan_mode else tk.RAISED)
        except Exception as e:
            logging.error(f"Erreur dans toggle_pan_mode: {str(e)}")

    def update_position_info(self):
        """Met à jour l'info de position"""
        try:
            if self.samples:
                total = len(self.samples)
                start = self.current_view_start + 1
                end = min(total, self.current_view_start + self.current_view_window)
                self.position_label.config(text=f"Position: {start}-{end}/{total} échantillons")

                slider_pos = (self.current_view_start / total) * 100 if total > 0 else 0
                self.slider_update_in_progress = True
                try:
                    self.time_slider.set(slider_pos)
                    if hasattr(self, 'time_slider_fs'):
                        self.time_slider_fs.set(slider_pos)
                finally:
                    self.slider_update_in_progress = False
            else:
                self.position_label.config(text="Position: 0/0 échantillons")
                self.slider_update_in_progress = True
                try:
                    self.time_slider.set(0)
                    if hasattr(self, 'time_slider_fs'):
                        self.time_slider_fs.set(0)
                finally:
                    self.slider_update_in_progress = False
        except Exception as e:
            logging.error(f"Erreur dans update_position_info: {str(e)}")

    def open_fullscreen_graphs(self):
        """Ouvre les graphiques en mode plein écran"""
        if self.fullscreen_window and self.fullscreen_window.winfo_exists():
            self.fullscreen_window.lift()
            return

        # Créer la fenêtre plein écran
        self.fullscreen_window = tk.Toplevel(self.master)
        self.fullscreen_window.title("Graphiques WiFi - Mode Plein Écran")
        self.fullscreen_window.state('zoomed')

        # Raccourcis clavier identiques en plein écran

        self.fullscreen_window.bind('<Left>', self.on_left_key)
        self.fullscreen_window.bind('<Right>', self.on_right_key)
        self.fullscreen_window.bind('<Home>', self.on_home_key)
        self.fullscreen_window.bind('<End>', self.on_end_key)
        self.fullscreen_window.bind('<space>', self.on_space_key)


        # Créer les graphiques pour la fenêtre plein écran
        self.setup_fullscreen_graphs()

        # Bouton pour fermer
        close_frame = ttk.Frame(self.fullscreen_window)
        close_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Button(
            close_frame,
            text="❌ Fermer le plein écran",
            command=self.close_fullscreen_graphs
        ).pack(side=tk.RIGHT)

        ttk.Label(
            close_frame,
            text="📊 Graphiques WiFi - Mode Présentation",
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)

    def setup_fullscreen_graphs(self):
        """Configure les graphiques en mode plein écran"""
        # Contrôles de navigation en plein écran
        nav_frame_fs = ttk.LabelFrame(self.fullscreen_window, text="🎛️ Navigation", padding=5)
        nav_frame_fs.pack(fill=tk.X, padx=10, pady=5)

        # Reproduction des contrôles principaux
        nav_buttons_fs = ttk.Frame(nav_frame_fs)
        nav_buttons_fs.pack(fill=tk.X)

        self.realtime_check_fs = ttk.Checkbutton(
            nav_buttons_fs,
            text="⏱️ Temps réel",
            variable=self.realtime_var,
            command=self.toggle_realtime_mode
        )
        self.realtime_check_fs.pack(side=tk.LEFT, padx=10)

        nav_controls_fs = ttk.Frame(nav_buttons_fs)
        nav_controls_fs.pack(side=tk.RIGHT)

        # Bouton pan en plein écran
        self.pan_button_fs = ttk.Button(nav_controls_fs, text="🖱️", command=self.toggle_pan_mode, width=3)
        self.pan_button_fs.pack(side=tk.LEFT, padx=1)

        for text, command in [("⏮️", self.go_to_start), ("⏪", self.go_previous),
                             ("⏸️", self.pause_navigation), ("⏩", self.go_next), ("⏭️", self.go_to_end)]:
            ttk.Button(nav_controls_fs, text=text, command=command, width=3).pack(side=tk.LEFT, padx=1)

        # Slider temporel en plein écran
        slider_frame_fs = ttk.Frame(nav_frame_fs)
        slider_frame_fs.pack(fill=tk.X, pady=5)

        ttk.Label(slider_frame_fs, text="Position:").pack(side=tk.LEFT)
        self.time_slider_fs = ttk.Scale(
            slider_frame_fs,
            from_=0, to=100,
            orient=tk.HORIZONTAL,
            command=self.on_slider_change
        )
        self.time_slider_fs.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Info position en plein écran
        self.position_label_fs = ttk.Label(nav_frame_fs, text="Position: 0/0 échantillons")
        self.position_label_fs.pack()

        # Graphiques en plein écran
        self.fig_fs = Figure(figsize=(16, 10))
        self.fig_fs.subplots_adjust(hspace=0.3)

        # Signal en plein écran
        self.ax1_fs = self.fig_fs.add_subplot(211)
        self.ax1_fs.set_title("Force du signal WiFi", fontsize=16)
        self.ax1_fs.set_ylabel("Signal (dBm)", fontsize=12)
        self.ax1_fs.grid(True, alpha=0.3)
        self.signal_line_fs, = self.ax1_fs.plot([], [], 'b-', linewidth=3, label="Signal")
        self.ax1_fs.set_ylim(-90, -30)
        self.ax1_fs.legend(fontsize=12)

        # Graphique de la qualité en plein écran
        self.ax2_fs = self.fig_fs.add_subplot(212)
        self.ax2_fs.set_title("Qualité de la connexion", fontsize=16)
        self.ax2_fs.set_ylabel("Qualité (%)", fontsize=12)
        self.ax2_fs.set_xlabel("Échantillons", fontsize=12)
        self.ax2_fs.grid(True, alpha=0.3)
        self.quality_line_fs, = self.ax2_fs.plot([], [], 'g-', linewidth=3, label="Qualité")
        self.ax2_fs.set_ylim(0, 100)
        self.ax2_fs.legend(fontsize=12)

        # Canvas plein écran
        self.canvas_fs = FigureCanvasTkAgg(self.fig_fs, master=self.fullscreen_window)
        self.canvas_fs.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Toolbar plein écran
        toolbar_frame_fs = ttk.Frame(self.fullscreen_window)
        toolbar_frame_fs.pack(fill=tk.X, padx=10)
        self.toolbar_fs = NavigationToolbar2Tk(self.canvas_fs, toolbar_frame_fs)
        self.toolbar_fs.update()
          # Mettre à jour les graphiques plein écran
        self.update_fullscreen_display()

    def close_fullscreen_graphs(self):
        """Ferme la fenêtre plein écran"""
        if self.fullscreen_window and self.fullscreen_window.winfo_exists():
            try:
                self.fullscreen_window.unbind('<Left>')
                self.fullscreen_window.unbind('<Right>')
                self.fullscreen_window.unbind('<Home>')
                self.fullscreen_window.unbind('<End>')
                self.fullscreen_window.unbind('<space>')
            except Exception:
                pass
            self.fullscreen_window.destroy()
        self.fullscreen_window = None

    def update_fullscreen_display(self):
        """Met à jour l'affichage en mode plein écran"""
        if not self.fullscreen_window or not self.fullscreen_window.winfo_exists():
            return

        if not self.samples:
            return

        try:
            # Déterminer la plage d'affichage
            if self.is_real_time:
                start_idx = max(0, len(self.samples) - self.current_view_window)
                end_idx = len(self.samples)
            else:
                start_idx = self.current_view_start
                end_idx = min(len(self.samples), start_idx + self.current_view_window)

            # Extraire les données
            display_samples = self.samples[start_idx:end_idx]
            if not display_samples:
                return

            signals = [s.signal_strength for s in display_samples]
            qualities = [s.quality for s in display_samples]
            x_data = range(len(signals))

            # Vérifier que nous avons des données valides
            if not signals or not qualities:
                return

            # Mettre à jour les lignes avec protection
            try:
                self.signal_line_fs.set_data(x_data, signals)
                self.quality_line_fs.set_data(x_data, qualities)

                # Ajuster les axes avec valeurs valides
                if len(signals) > 0:
                    self.ax1_fs.set_xlim(0, max(1, len(signals)))
                    self.ax2_fs.set_xlim(0, max(1, len(qualities)))

                # Marquer les alertes
                self.mark_alerts_on_fullscreen()

                # Rafraîchir avec gestion d'erreur
                self.canvas_fs.draw_idle()  # Utiliser draw_idle() au lieu de draw()

            except Exception as graph_error:
                logging.warning(f"Erreur lors de la mise à jour des graphiques plein écran: {graph_error}")

            # Mettre à jour les infos de position
            if hasattr(self, 'position_label_fs'):
                total = len(self.samples)
                start = start_idx + 1
                end = end_idx
                self.position_label_fs.config(text=f"Position: {start}-{end}/{total} échantillons")

        except Exception as e:
            logging.error(f"Erreur générale dans update_fullscreen_display: {e}")
            # Continuer sans faire crasher l'application

    def mark_alerts_on_fullscreen(self):
        """Marque les alertes sur les graphiques plein écran"""
        # Effacer les anciens marqueurs
        for marker in getattr(self, 'alert_markers_fs', []):
            try:
                marker.remove()
            except:
                pass
        self.alert_markers_fs = []

        if not hasattr(self, 'samples') or not self.samples:
            return

        # Déterminer la plage d'affichage
        if self.is_real_time:
            start_idx = max(0, len(self.samples) - self.current_view_window)
        else:
            start_idx = self.current_view_start

        # Marquer les points avec alertes
        for i, sample in enumerate(self.samples[start_idx:start_idx + self.current_view_window]):
            # Vérifier si ce sample avait des alertes
            if (sample.signal_strength < -85 or sample.quality < 20 or
                (hasattr(sample, 'raw_data') and self._check_rate_alerts(sample))):

                # Marquer sur les deux graphiques
                marker1 = self.ax1_fs.axvline(x=i, color='red', alpha=0.7, linewidth=2)
                marker2 = self.ax2_fs.axvline(x=i, color='red', alpha=0.7, linewidth=2)

                self.alert_markers_fs.extend([marker1, marker2])

    def _check_rate_alerts(self, sample):
        """Vérifie les alertes de débit pour un échantillon"""
        try:
            if not hasattr(sample, 'raw_data') or not sample.raw_data:
                return False

            tx_rate = int(sample.raw_data.get('TransmitRate', '0 Mbps').split()[0])
            rx_rate = int(sample.raw_data.get('ReceiveRate', '0 Mbps').split()[0])

            # Nouveaux seuils réalistes
            return (tx_rate < 10 and rx_rate < 2) or (tx_rate < 50 and rx_rate < 5)
        except:
            return False

    def add_to_wifi_history(self, sample, alerts, timestamp):
        """Ajoute un événement à l'historique WiFi"""
        if hasattr(self, 'wifi_history_text'):
            # Créer l'entrée d'historique
            entry_text = f"{timestamp} | Signal: {sample.signal_strength} dBm | Qualité: {sample.quality}%"

            if alerts:
                entry_text += f" | ⚠️ {len(alerts)} alerte(s)\n"
                for alert in alerts:
                    entry_text += f"    → {alert}\n"
            else:
                entry_text += " | ✅ OK\n"

            # Ajouter au début du texte
            self.wifi_history_text.insert('1.0', entry_text + "\n")

    def update_advanced_wifi_stats(self):
        """Met à jour les statistiques avancées"""
        if not hasattr(self, 'wifi_advanced_stats_text') or not self.samples:
            return

        # Calculer les statistiques avancées
        signals = [s.signal_strength for s in self.samples]
        qualities = [s.quality for s in self.samples]

        # Statistiques de base
        stats_text = "=== STATISTIQUES AVANCÉES ===\n\n"
        stats_text += f"📊 Nombre total d'échantillons: {len(self.samples)}\n"
        stats_text += f"⏱️ Durée d'analyse: {self._get_analysis_duration()}\n\n"

        # Signal
        stats_text += "📶 ANALYSE DU SIGNAL:\n"
        stats_text += f"• Moyenne: {np.mean(signals):.1f} dBm\n"
        stats_text += f"• Médiane: {np.median(signals):.1f} dBm\n"
        stats_text += f"• Écart-type: {np.std(signals):.1f} dBm\n"
        stats_text += f"• Min/Max: {min(signals):.1f} / {max(signals):.1f} dBm\n\n"

        # Qualité
        stats_text += "🎯 ANALYSE DE LA QUALITÉ:\n"
        stats_text += f"• Moyenne: {np.mean(qualities):.1f}%\n"
        stats_text += f"• Médiane: {np.median(qualities):.1f}%\n"
        stats_text += f"• Écart-type: {np.std(qualities):.1f}%\n"
        stats_text += f"• Min/Max: {min(qualities):.1f} / {max(qualities):.1f}%\n\n"

        # Alertes
        total_alerts = self._count_total_alerts()
        alert_rate = (total_alerts / len(self.samples)) * 100 if self.samples else 0
        stats_text += "🚨 ANALYSE DES ALERTES:\n"
        stats_text += f"• Total d'alertes: {total_alerts}\n"
        stats_text += f"• Taux d'alertes: {alert_rate:.1f}%\n"

        # Mettre à jour le texte
        self.wifi_advanced_stats_text.delete('1.0', tk.END)
        self.wifi_advanced_stats_text.insert('1.0', stats_text)

    def _get_analysis_duration(self):
        """Calcule la durée d'analyse"""
        if len(self.samples) < 2:
            return "< 1 seconde"

        first_time = self.samples[0].timestamp
        last_time = self.samples[-1].timestamp

        try:
            if isinstance(first_time, str):
                first_dt = datetime.strptime(first_time, "%H:%M:%S")
                last_dt = datetime.strptime(last_time, "%H:%M:%S")
                duration = last_dt - first_dt
            else:
                duration = last_time - first_time

            total_seconds = duration.total_seconds()
            if total_seconds < 60:
                return f"{total_seconds:.1f} secondes"
            elif total_seconds < 3600:
                return f"{total_seconds/60:.1f} minutes"
            else:
                return f"{total_seconds/3600:.1f} heures"
        except:
            return f"~{len(self.samples)} échantillons"

    def _count_total_alerts(self):
        """Compte le nombre total d'alertes"""
        total = 0
        for sample in self.samples:
            if sample.signal_strength < -85 or sample.quality < 20:
                total += 1
            elif self._check_rate_alerts(sample):
                total += 1
        return total

    def generate_final_network_report(self):
        """Génère le rapport final de l'analyse réseau"""
        if not hasattr(self, 'wifi_final_report_text') or not self.samples:
            return

        # Calculer les métriques du rapport
        signals = [s.signal_strength for s in self.samples]
        qualities = [s.quality for s in self.samples]
        total_alerts = self._count_total_alerts()

        # Calcul du score global (amélioré)
        signal_score = self._calculate_signal_score(signals)
        quality_score = self._calculate_quality_score(qualities)
        alert_score = self._calculate_alert_score(total_alerts, len(self.samples))

        global_score = int((signal_score + quality_score + alert_score) / 3)

        # Génération du rapport
        report = f"""🏆 RAPPORT FINAL - QUALITÉ RÉSEAU WIFI
============================================================

📊 SCORE GLOBAL : {global_score}/100
{self._get_score_status(global_score)}

📋 INFORMATIONS GÉNÉRALES
• Durée d'analyse : {self._get_analysis_duration()}
• Échantillons collectés : {len(self.samples)}
• Intervalle d'échantillonnage : 1.0 secondes

📶 ANALYSE DU SIGNAL WIFI
• Signal moyen : {np.mean(signals):.1f} dBm
• Signal minimum : {min(signals)} dBm
• Signal maximum : {max(signals)} dBm
• Variation : {max(signals) - min(signals)} dBm
{self._get_signal_evaluation(np.mean(signals))}

🎯 ANALYSE DE LA QUALITÉ
• Qualité moyenne : {np.mean(qualities):.1f}%
• Qualité minimum : {min(qualities):.0f}%
• Qualité maximum : {max(qualities):.0f}%
• Temps avec qualité > 70% : {self._calculate_good_quality_time(qualities):.1f}%
{self._get_quality_evaluation(np.mean(qualities))}

🚨 ANALYSE DES ALERTES
• Total d'alertes : {total_alerts}
• Pourcentage d'alertes : {(total_alerts/len(self.samples)*100):.1f}%
{self._get_alert_evaluation(total_alerts, len(self.samples))}

💡 RECOMMANDATIONS
{self._get_recommendations(global_score, np.mean(signals), np.mean(qualities), total_alerts)}

📝 CONCLUSION
{self._get_conclusion(global_score)}

📅 Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
============================================================
"""

        # Afficher le rapport
        self.wifi_final_report_text.delete('1.0', tk.END)
        self.wifi_final_report_text.insert('1.0', report)

    def _calculate_signal_score(self, signals):
        """Calcule le score du signal (0-100)"""
        avg_signal = np.mean(signals)
        if avg_signal >= -60:
            return 100
        elif avg_signal >= -70:
            return 90
        elif avg_signal >= -80:
            return 70
        elif avg_signal >= -85:
            return 50
        else:
            return 30

    def _calculate_quality_score(self, qualities):
        """Calcule le score de qualité (0-100)"""
        avg_quality = np.mean(qualities)
        return min(100, max(0, int(avg_quality)))

    def _calculate_alert_score(self, total_alerts, total_samples):
        """Calcule le score basé sur les alertes (0-100)"""
        if total_samples == 0:
            return 100

        alert_rate = total_alerts / total_samples
        if alert_rate < 0.05:  # Moins de 5% d'alertes
            return 100
        elif alert_rate < 0.15:  # Moins de 15% d'alertes
            return 80
        elif alert_rate < 0.30:  # Moins de 30% d'alertes
            return 60
        else:
            return 30

    def _get_score_status(self, score):
        """Retourne le statut basé sur le score"""
        if score >= 85:
            return "✅ EXCELLENT - Aucune action requise"
        elif score >= 70:
            return "⚠️ BON - Améliorations mineures possibles"
        elif score >= 50:
            return "⚠️ MOYEN - Améliorations possibles"
        else:
            return "❌ PROBLÉMATIQUE - Intervention nécessaire"

    def _get_signal_evaluation(self, avg_signal):
        """Évalue la qualité du signal"""
        if avg_signal >= -60:
            return "✅ Signal excellent (-50 à -60 dBm)"
        elif avg_signal >= -70:
            return "✅ Signal très bon (-60 à -70 dBm)"
        elif avg_signal >= -80:
            return "⚠️ Signal acceptable (-70 à -80 dBm)"
        else:
            return "❌ Signal faible (< -80 dBm)"

    def _get_quality_evaluation(self, avg_quality):
        """Évalue la qualité de connexion"""
        if avg_quality >= 80:
            return "✅ Qualité excellente (> 80%)"
        elif avg_quality >= 60:
            return "✅ Qualité bonne (60-80%)"
        elif avg_quality >= 40:
            return "⚠️ Qualité moyenne (40-60%)"
        else:
            return "❌ Qualité faible (< 40%)"

    def _get_alert_evaluation(self, total_alerts, total_samples):
        """Évalue le niveau d'alertes"""
        if total_samples == 0:
            return "✅ Aucune donnée"

        alert_rate = total_alerts / total_samples
        if alert_rate < 0.05:
            return "✅ Très peu d'alertes - réseau stable"
        elif alert_rate < 0.15:
            return "✅ Peu d'alertes - surveillance recommandée"
        elif alert_rate < 0.30:
            return "⚠️ Quelques alertes - surveillance recommandée"
        else:
            return "❌ Beaucoup d'alertes - intervention nécessaire"

    def _calculate_good_quality_time(self, qualities):
        """Calcule le pourcentage de temps avec bonne qualité"""
        good_quality_count = sum(1 for q in qualities if q > 70)
        return (good_quality_count / len(qualities)) * 100 if qualities else 0

    def _get_recommendations(self, score, avg_signal, avg_quality, total_alerts):
        """Génère les recommandations"""
        if score >= 85:
            return "✅ Réseau en excellent état - Aucune action requise\n   • Continuer la surveillance périodique\n   • Documenter cette configuration pour référence"
        elif score >= 70:
            return "✅ Réseau en bon état - Surveillance recommandée\n   • Vérifier périodiquement les performances\n   • Surveiller les alertes sporadiques"
        elif score >= 50:
            return "⚠️ Réseau nécessitant des améliorations\n   • Analyser les causes des alertes\n   • Vérifier la position des points d'accès\n   • Contrôler les interférences"
        else:
            return "❌ Réseau nécessitant une intervention urgente\n   • Vérifier la couverture WiFi\n   • Repositionner les points d'accès\n   • Analyser les sources d'interférences\n   • Contacter le support technique"

    def _get_conclusion(self, score):
        """Génère la conclusion du rapport"""
        if score >= 85:
            return "Votre réseau WiFi offre d'excellentes performances. La qualité de service est optimale pour les opérations critiques."
        elif score >= 70:
            return "Votre réseau WiFi offre de bonnes performances avec quelques améliorations mineures possibles."
        elif score >= 50:
            return "Votre réseau WiFi offre des performances correctes mais pourrait bénéficier de quelques améliorations pour optimiser la stabilité et les performances."
        else:
            return "Votre réseau WiFi présente des problèmes significatifs qui nécessitent une attention immédiate pour assurer un service fiable."

    def update_wifi_history_display(self):
        """Met à jour l'affichage de l'historique WiFi avec les événements récents"""
        if not hasattr(self, 'wifi_history_text') or not self.samples:
            return

        # Prendre les 10 derniers échantillons pour l'historique
        recent_samples = self.samples[-10:] if len(self.samples) >= 10 else self.samples

        # Vider le texte actuel
        self.wifi_history_text.delete('1.0', tk.END)

        history_text = "=== HISTORIQUE WIFI RÉCENT ===\n\n"

        for i, sample in enumerate(reversed(recent_samples)):
            timestamp = datetime.now().strftime('%H:%M:%S')

            # Vérifier s'il y a des alertes pour cet échantillon
            alerts = []
            if sample.signal_strength < -80:
                alerts.append(f"Signal faible: {sample.signal_strength} dBm")
            if sample.quality < 40:
                alerts.append(f"Qualité faible: {sample.quality}%")

            # Créer l'entrée d'historique
            status_icon = "⚠️" if alerts else "✅"
            history_text += f"{status_icon} {timestamp} | Signal: {sample.signal_strength} dBm | Qualité: {sample.quality}%"

            if alerts:
                history_text += f" | {len(alerts)} alerte(s)\n"
                for alert in alerts:
                    history_text += f"    → {alert}\n"
            else:
                history_text += " | Réseau OK\n"

            history_text += "\n"

        # Ajouter les statistiques globales
        if len(self.samples) > 0:
            avg_signal = sum(s.signal_strength for s in self.samples) / len(self.samples)
            avg_quality = sum(s.quality for s in self.samples) / len(self.samples)

            history_text += "\n=== RÉSUMÉ GLOBAL ===\n"
            history_text += f"📊 Échantillons analysés: {len(self.samples)}\n"
            history_text += f"📶 Signal moyen: {avg_signal:.1f} dBm\n"
            history_text += f"🎯 Qualité moyenne: {avg_quality:.1f}%\n"

            # État général du réseau
            if avg_signal > -70 and avg_quality > 60:
                history_text += "✅ État réseau: EXCELLENT\n"
            elif avg_signal > -80 and avg_quality > 40:
                history_text += "🟡 État réseau: CORRECT\n"
            else:
                history_text += "🔴 État réseau: PROBLÉMATIQUE\n"

        # Insérer le texte
        self.wifi_history_text.insert('1.0', history_text)


def main():
    """Point d'entrée principal de l'application"""
    try:
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('wifi_analyzer.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        logging.info("Démarrage de l'application WiFi Analyzer")

        # Créer la fenêtre principale
        root = tk.Tk()

        # Créer l'interface utilisateur
        app = NetworkAnalyzerUI(root)
        # Configuration de la fermeture propre
        def on_closing():
            logging.info("Fermeture de l'application")
            if app.amr_monitor:
                app.amr_monitor.stop()
            try:
                root.unbind('<Left>')
                root.unbind('<Right>')
                root.unbind('<Home>')
                root.unbind('<End>')
                root.unbind('<space>')
            except Exception:
                pass
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Lancer la boucle principale
        logging.info("Interface utilisateur prête")
        root.mainloop()

    except Exception as e:
        logging.error(f"Erreur lors du démarrage de l'application: {e}")
        messagebox.showerror("Erreur", f"Impossible de démarrer l'application:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
