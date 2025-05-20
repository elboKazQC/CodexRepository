# -*- coding: utf-8 -*-
import sys
import json
import logging
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import List, Optional
import os
from dotenv import load_dotenv

# Charger automatiquement les variables d'environnement depuis un fichier .env
load_dotenv()

from network_analyzer import NetworkAnalyzer
from wifi.wifi_collector import WifiSample
from network_scanner import scan_wifi
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
        self.scan_results: List[dict] = []

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
        self.setup_graphs()

        # Variables pour les mises à jour
        self.update_interval = 1000  # ms
        self.max_samples = 100

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
        self.stop_button.pack(fill=tk.X, pady=5)

        self.scan_button = ttk.Button(
            control_frame,
            text="\U0001F50D Scanner",
            command=self.scan_nearby_aps
        )
        self.scan_button.pack(fill=tk.X, pady=5)

        self.export_scan_button = ttk.Button(
            control_frame,
            text="\U0001F4C3 Exporter le scan",
            command=self.export_scan_results,
            state=tk.DISABLED
        )
        self.export_scan_button.pack(fill=tk.X, pady=5)

        # Zone de statistiques
        stats_frame = ttk.LabelFrame(control_frame, text="Statistiques", padding=5)
        stats_frame.pack(fill=tk.X, pady=10)

        self.stats_text = tk.Text(stats_frame, height=6, width=30)
        self.stats_text.pack(fill=tk.X, pady=5)

        # Panneau des graphiques et alertes (droite)
        self.viz_frame = ttk.Frame(self.wifi_frame)
        self.viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.scan_frame = ttk.LabelFrame(self.viz_frame, text="R\u00e9seaux d\u00e9tect\u00e9s", padding=5)
        self.scan_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

        columns = ("ssid", "signal", "channel", "band")
        self.scan_tree = ttk.Treeview(self.scan_frame, columns=columns, show="headings", height=8)
        for col, title in zip(columns, ["SSID", "Signal (dBm)", "Canal", "Bande"]):
            self.scan_tree.heading(col, text=title)
            self.scan_tree.column(col, width=100)
        self.scan_tree.pack(fill=tk.BOTH, expand=True)

        # Les graphiques seront ajoutés ici par setup_graphs()

        # Zone d'alertes
        self.alerts_frame = ttk.LabelFrame(self.viz_frame, text="Zones problématiques détectées", padding=5)
        self.alerts_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        self.wifi_alert_text = tk.Text(self.alerts_frame, height=4, wrap=tk.WORD)
        wifi_scroll = ttk.Scrollbar(self.alerts_frame, command=self.wifi_alert_text.yview)
        self.wifi_alert_text.configure(yscrollcommand=wifi_scroll.set)
        self.wifi_alert_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        wifi_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # === Onglet Moxa ===
        self.moxa_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.moxa_frame, text="Analyse Moxa")

        # PanedWindow pour rendre l'onglet ajustable
        paned = ttk.Panedwindow(self.moxa_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        top_pane = ttk.Frame(paned)
        bottom_pane = ttk.Frame(paned)
        paned.add(top_pane, weight=1)
        paned.add(bottom_pane, weight=1)

        # --- Contenu du volet supérieur ---
        input_frame = ttk.LabelFrame(top_pane, text="Collez vos logs Moxa ici :", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.moxa_input = tk.Text(input_frame, wrap=tk.WORD)
        input_scroll = ttk.Scrollbar(input_frame, command=self.moxa_input.yview)
        self.moxa_input.configure(yscrollcommand=input_scroll.set)
        self.moxa_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        input_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        config_frame = ttk.LabelFrame(
            top_pane,
            text="Configuration Moxa actuelle (JSON) :",
            padding=10,
        )
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.moxa_config_text = tk.Text(config_frame, height=8, wrap=tk.WORD)
        cfg_scroll = ttk.Scrollbar(config_frame, command=self.moxa_config_text.yview)
        self.moxa_config_text.configure(yscrollcommand=cfg_scroll.set)
        self.moxa_config_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cfg_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.moxa_config_text.insert('1.0', json.dumps(self.current_config, indent=2))

        params_frame = ttk.LabelFrame(top_pane, text="Paramètres supplémentaires :", padding=10)
        params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.moxa_params_text = tk.Text(params_frame, height=4, wrap=tk.WORD)
        params_scroll = ttk.Scrollbar(params_frame, command=self.moxa_params_text.yview)
        self.moxa_params_text.configure(yscrollcommand=params_scroll.set)
        self.moxa_params_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        params_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Label(
            params_frame,
            text="Indiquez ici tout contexte supplémentaire (ex. roaming=snr)"
        ).pack(anchor=tk.W, pady=(5, 0))

        config_btn_frame = ttk.Frame(top_pane)
        config_btn_frame.pack(pady=5)
        ttk.Button(config_btn_frame, text="Charger config", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="Éditer config", command=self.edit_config).pack(side=tk.LEFT, padx=5)

        self.analyze_button = ttk.Button(
            top_pane,
            text="🔍 Analyser les logs",
            style="Analyze.TButton",
            command=self.analyze_moxa_logs
        )
        self.analyze_button.pack(pady=10)

        # --- Contenu du volet inférieur ---
        results_frame = ttk.LabelFrame(bottom_pane, text="Résultats de l'analyse :", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.moxa_results = tk.Text(results_frame, wrap=tk.WORD)
        results_scroll = ttk.Scrollbar(results_frame, command=self.moxa_results.yview)
        self.moxa_results.configure(yscrollcommand=results_scroll.set)
        self.moxa_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.export_button = ttk.Button(
            bottom_pane,
            text="💾 Exporter l'analyse",
            command=self.export_data,
            state=tk.DISABLED
        )
        self.export_button.pack(pady=5)

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
        parent = getattr(self, "viz_frame", self.wifi_frame)
        before_widget = getattr(self, "alerts_frame", None)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        pack_opts = {"fill": tk.BOTH, "expand": True, "padx": 5, "pady": 5}
        if before_widget is not None:
            pack_opts["before"] = before_widget
        self.canvas.get_tk_widget().pack(**pack_opts)

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

    def scan_nearby_aps(self):
        """Scanne les points d'accès WiFi proches et met à jour la liste."""
        try:
            results = scan_wifi()
            self.scan_results = results

            for row in self.scan_tree.get_children():
                self.scan_tree.delete(row)

            for ap in results:
                self.scan_tree.insert(
                    "",
                    "end",
                    values=(
                        ap.get("ssid", ""),
                        ap.get("signal", ""),
                        ap.get("channel", ""),
                        ap.get("frequency", ""),
                    ),
                )

            if results:
                self.export_scan_button.config(state=tk.NORMAL)
        except Exception as e:
            self.show_error(f"Erreur lors du scan: {e}")

    def export_scan_results(self):
        """Exporte les résultats du scan WiFi au format CSV."""
        if not self.scan_results:
            messagebox.showinfo("Export", "Aucun résultat à exporter")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv")],
            title="Exporter le scan",
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["SSID", "Signal(dBm)", "Canal", "Bande"])
                    for ap in self.scan_results:
                        writer.writerow(
                            [
                                ap.get("ssid", ""),
                                ap.get("signal", ""),
                                ap.get("channel", ""),
                                ap.get("frequency", ""),
                            ]
                        )
                messagebox.showinfo("Export", f"Résultats exportés vers {filepath}")
            except Exception as e:
                self.show_error(f"Erreur export CSV: {e}")

    def analyze_moxa_logs(self):
        """Analyse les logs Moxa collés avec OpenAI"""
        try:
            logs = self.moxa_input.get('1.0', tk.END).strip()
            if not logs:
                messagebox.showwarning(
                    "Analyse impossible",
                    "Veuillez coller des logs Moxa à analyser"
                )
                return

            # Vérifier la clé API OpenAI dans l'environnement
            api_key = os.getenv("OPENAI_API_KEY")
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

            # Récupérer les paramètres complémentaires saisis
            params_text = self.moxa_params_text.get('1.0', tk.END).strip()

            # Appel à l'API OpenAI avec la configuration courante
            analysis = analyze_moxa_logs(logs, self.current_config, params_text or None)

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

        if alerts:
            msg = f"Position au {datetime.now().strftime('%H:%M:%S')} :\n"
            msg += "\n".join(alerts)
            self.wifi_alert_text.delete('1.0', tk.END)
            self.wifi_alert_text.insert('1.0', msg)

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
            pass

        # Mise à jour du texte
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
        self.wifi_alert_text.insert('1.0', f"{current_time} - {message}\n")

    def show_error(self, message: str):
        """Affiche une erreur"""
        messagebox.showerror("Erreur", message)
        self.update_status(f"ERREUR: {message}")


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
