# -*- coding: utf-8 -*-
import sys
import json
import logging
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
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
        self.master.state('zoomed')

        # Initialisation des composants
        self.analyzer = NetworkAnalyzer()
        self.samples: List[WifiSample] = []
        self.amr_ips: List[str] = []
        self.amr_monitor: Optional[AMRMonitor] = None

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

        # Zone de statistiques réduite pour optimiser l'espace
        self.stats_text = tk.Text(stats_frame, height=10, width=35)
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
        wifi_advanced_scroll.pack(side=tk.RIGHT, fill=tk.Y)# === Onglet Moxa ===
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
        self.moxa_config_text.insert('1.0', json.dumps(self.current_config, indent=2))        # Boutons de configuration
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
        """Configure les graphiques"""
        # Figure principale
        self.fig = Figure(figsize=(10, 6))
        self.fig.subplots_adjust(hspace=0.3)

        # Graphique du signal
        self.ax1 = self.fig.add_subplot(211)
        self.ax1.set_title("Force du signal WiFi")
        self.ax1.set_ylabel("Signal (dBm)")
        self.ax1.grid(True)
        self.signal_line, = self.ax1.plot([], [], 'b-', label="Signal")
        self.ax1.set_ylim(-90, -30)
        self.ax1.legend()

        # Graphique de la qualité
        self.ax2 = self.fig.add_subplot(212)
        self.ax2.set_title("Qualité de la connexion")
        self.ax2.set_ylabel("Qualité (%)")
        self.ax2.grid(True)
        self.quality_line, = self.ax2.plot([], [], 'g-', label="Qualité")
        self.ax2.set_ylim(0, 100)
        self.ax2.legend()

        # Canvas Matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.wifi_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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

        # Force du signal
        if sample.signal_strength < -80:
            alerts.append(f"🔴 Signal CRITIQUE : {sample.signal_strength} dBm")
        elif sample.signal_strength < -70:
            alerts.append(f"⚠️ Signal faible : {sample.signal_strength} dBm")

        # Qualité
        if sample.quality < 20:
            alerts.append(f"🔴 Qualité CRITIQUE : {sample.quality}%")
        elif sample.quality < 40:
            alerts.append(f"⚠️ Qualité faible : {sample.quality}%")

        # Débits
        try:
            tx_rate = int(sample.raw_data.get('TransmitRate', '0 Mbps').split()[0])
            rx_rate = int(sample.raw_data.get('ReceiveRate', '0 Mbps').split()[0])
            if min(tx_rate, rx_rate) < 24:
                alerts.append(
                    f"⚠️ Débit insuffisant :\n"
                    f"   TX: {tx_rate} Mbps, RX: {rx_rate} Mbps"
                )
        except (ValueError, IndexError, KeyError):
            pass

        # Mise à jour onglet Alertes
        if alerts:
            msg = f"Position au {timestamp} :\n"
            msg += "\n".join(alerts)
            self.wifi_alert_text.delete('1.0', tk.END)
            self.wifi_alert_text.insert('1.0', msg)

        # Ajouter à l'historique (même si pas d'alertes)
        self.add_to_wifi_history(sample, alerts, timestamp)

        # Mettre à jour les stats avancées
        self.update_advanced_wifi_stats()

    def update_display(self):
        """Met à jour les graphiques"""
        if not self.samples:
            return

        # Données pour les graphiques
        times = [s.timestamp for s in self.samples[-self.max_samples:]]
        signals = [s.signal_strength for s in self.samples[-self.max_samples:]]
        qualities = [s.quality for s in self.samples[-self.max_samples:]]

        # Mise à jour des lignes
        self.signal_line.set_data(range(len(signals)), signals)
        self.quality_line.set_data(range(len(qualities)), qualities)

        # Mise à jour des axes
        self.ax1.set_xlim(0, len(signals))
        self.ax2.set_xlim(0, len(qualities))

        # Rafraîchissement
        self.canvas.draw()

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
                'quality': 0,                'alerts': [f"📢 {message}"]
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

    def add_to_wifi_history(self, sample, alerts, timestamp):
        """Ajoute une entrée à l'historique WiFi"""
        entry = {
            'timestamp': timestamp,
            'signal': sample.signal_strength,
            'quality': sample.quality,
            'alerts': alerts
        }

        self.wifi_history_entries.append(entry)

        # Limiter la taille de l'historique
        if len(self.wifi_history_entries) > self.max_history_entries:
            self.wifi_history_entries = self.wifi_history_entries[-self.max_history_entries:]

        # Mettre à jour l'affichage de l'historique (les 50 dernières entrées)
        self.update_wifi_history_display()

    def update_wifi_history_display(self):
        """Met à jour l'affichage de l'historique WiFi"""
        self.wifi_history_text.delete('1.0', tk.END)

        # Afficher les 50 dernières entrées
        recent_entries = self.wifi_history_entries[-50:]

        for entry in reversed(recent_entries):  # Plus récent en premier
            status_icon = "🟢" if not entry['alerts'] else "🔴"
            line = f"{status_icon} {entry['timestamp']} | Signal: {entry['signal']} dBm | Qualité: {entry['quality']}%"

            if entry['alerts']:
                line += f" | ⚠️ {len(entry['alerts'])} alerte(s)"

            self.wifi_history_text.insert(tk.END, line + "\n")

            # Ajouter les détails des alertes si présentes
            for alert in entry['alerts']:
                self.wifi_history_text.insert(tk.END, f"    → {alert}\n")

            self.wifi_history_text.insert(tk.END, "\n")

    def update_advanced_wifi_stats(self):
        """Met à jour les statistiques avancées"""
        if not self.samples:
            return

        self.wifi_advanced_stats_text.delete('1.0', tk.END)

        # Calculs statistiques avancés
        signal_values = [s.signal_strength for s in self.samples]
        quality_values = [s.quality for s in self.samples]

        # Statistiques globales
        stats = f"=== STATISTIQUES GLOBALES ===\n\n"
        stats += f"📊 Échantillons collectés: {len(self.samples)}\n"
        stats += f"⏰ Durée d'analyse: {len(self.samples)} secondes\n\n"

        # Statistiques du signal
        stats += f"=== SIGNAL WIFI ===\n"
        stats += f"📶 Signal actuel: {signal_values[-1]} dBm\n"
        stats += f"📈 Signal max: {max(signal_values)} dBm\n"
        stats += f"📉 Signal min: {min(signal_values)} dBm\n"
        stats += f"📊 Signal moyen: {sum(signal_values)/len(signal_values):.1f} dBm\n\n"

        # Statistiques de qualité
        stats += f"=== QUALITÉ ===\n"
        stats += f"🎯 Qualité actuelle: {quality_values[-1]}%\n"
        stats += f"🏆 Qualité max: {max(quality_values)}%\n"
        stats += f"⬇️ Qualité min: {min(quality_values)}%\n"
        stats += f"📊 Qualité moyenne: {sum(quality_values)/len(quality_values):.1f}%\n\n"

        # Analyse de tendances
        if len(signal_values) >= 10:
            recent_signal = signal_values[-10:]
            older_signal = signal_values[-20:-10] if len(signal_values) >= 20 else signal_values[:-10]

            recent_avg = sum(recent_signal) / len(recent_signal)
            older_avg = sum(older_signal) / len(older_signal) if older_signal else recent_avg

            stats += f"=== TENDANCES ===\n"
            if recent_avg > older_avg + 2:
                stats += "📈 Signal en amélioration\n"
            elif recent_avg < older_avg - 2:
                stats += "📉 Signal en dégradation\n"
            else:
                stats += "➡️ Signal stable\n"

        # Compteur d'alertes
        total_alerts = sum(len(entry['alerts']) for entry in self.wifi_history_entries)
        stats += f"\n=== ALERTES ===\n"
        stats += f"🚨 Total d'alertes: {total_alerts}\n"

        if self.wifi_history_entries:
            entries_with_alerts = len([e for e in self.wifi_history_entries if e['alerts']])
            percentage = (entries_with_alerts / len(self.wifi_history_entries)) * 100
            stats += f"📊 Pourcentage avec alertes: {percentage:.1f}%\n"

        self.wifi_advanced_stats_text.insert('1.0', stats)


class MoxaAnalyzerUI(NetworkAnalyzerUI):
    """Backward-compatible alias used in tests."""

    def __init__(self, master: tk.Tk):
        super().__init__(master)
        # Provide legacy attribute names expected by older tests
        self.logs_input_text = self.moxa_input
        self.results_text = self.moxa_results

    def analyze_logs_from_input(self, log_content=None):
        """Compatibility wrapper calling analyze_moxa_logs."""
        if log_content is not None:
            self.logs_input_text.delete("1.0", tk.END)
            self.logs_input_text.insert("1.0", log_content)
        self.analyze_moxa_logs()

    def _analyze_logs(self):
        """Legacy private method used in tests."""
        self.analyze_moxa_logs()

def main():
    """Point d'entrée de l'application"""
    try:
        from bootstrap_ui import BootstrapNetworkAnalyzerUI
        app = BootstrapNetworkAnalyzerUI()
        app.master.mainloop()
    except Exception as e:
        print(f"Erreur fatale: {str(e)}")
        messagebox.showerror("Erreur fatale", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
