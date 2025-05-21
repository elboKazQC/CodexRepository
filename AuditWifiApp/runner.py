"""Application entry point.

This module instantiates the different UI views and orchestrates their
interaction. The actual user interface components have been extracted
into ``ui.wifi_view`` and ``ui.moxa_view`` for clarity.
"""

from __future__ import annotations

import sys
import tkinter as tk

from tkinter import ttk, messagebox, filedialog, simpledialog
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    MATPLOTLIB_AVAILABLE = False
    plt = None
    FigureCanvasTkAgg = None  # type: ignore
    Figure = None  # type: ignore
import numpy as np
from typing import List, Optional

import os
from dotenv import load_dotenv


from network_analyzer import NetworkAnalyzer
from ui.wifi_view import WifiView
from ui.moxa_view import MoxaView
from network_scanner import scan_wifi  # re-exported for tests


load_dotenv()


class NetworkAnalyzerUI:
    """Main window coordinating the WiFi and Moxa views."""

    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("Analyseur R\u00e9seau WiFi & Moxa")
        self.master.state('zoomed')

        self.analyzer = NetworkAnalyzer()

        # Default configuration for the Moxa analyzer
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

        self.config_dir = os.path.join(os.path.dirname(__file__), "config")

        self.create_interface()

    # ------------------------------------------------------------------
    # Interface creation
    # ------------------------------------------------------------------
    def create_interface(self) -> None:
        """Create notebook with WiFi and Moxa tabs."""
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


        self.wifi_view = WifiView(self.notebook, self.analyzer)
        self.notebook.add(self.wifi_view.frame, text="Analyse WiFi")


        self.moxa_view = MoxaView(self.notebook, self.config_dir, self.default_config)
        self.notebook.add(self.moxa_view.frame, text="Analyse Moxa")

        # Expose some attributes for backward compatibility with tests
        self.start_button = self.wifi_view.start_button
        self.stop_button = self.wifi_view.stop_button
        self.scan_button = self.wifi_view.scan_button
        self.export_scan_button = self.wifi_view.export_scan_button
        self.scan_tree = self.wifi_view.scan_tree


    # ------------------------------------------------------------------
    # Delegated methods used by tests or other modules
    # ------------------------------------------------------------------
    def setup_graphs(self) -> None:
        self.wifi_view.setup_graphs()

    def start_collection(self) -> None:
        self.wifi_view.start_collection()

    def stop_collection(self) -> None:
        self.wifi_view.stop_collection()

    def scan_nearby_aps(self) -> None:
        self.wifi_view.scan_nearby_aps()

    def export_scan_results(self) -> None:
        self.wifi_view.export_scan_results()

    def export_data(self) -> None:
        self.wifi_view.export_data()

    # Moxa view delegations
    def analyze_moxa_logs(self) -> None:
        self.moxa_view.analyze_moxa_logs()

    def load_config(self) -> None:
        self.moxa_view.load_config()

    def edit_config(self) -> None:
        self.moxa_view.edit_config()

    # Utility wrappers
    def update_status(self, message: str) -> None:
        self.wifi_view.update_status(message)

    def update_data(self) -> None:
        """Delegate to WifiView to refresh displayed data."""
        self.wifi_view.update_data()

    def show_error(self, message: str) -> None:
        self.wifi_view.show_error(message)




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

        # Zone de statistiques
        stats_frame = ttk.LabelFrame(control_frame, text="Statistiques", padding=5)
        stats_frame.pack(fill=tk.X, pady=10)

        self.stats_text = tk.Text(stats_frame, height=6, width=30)
        self.stats_text.pack(fill=tk.X, pady=5)

        # Panneau des graphiques et alertes (droite)
        viz_frame = ttk.Frame(self.wifi_frame)
        viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Les graphiques seront ajoutés ici par setup_graphs()

        # Zone d'alertes
        alerts_frame = ttk.LabelFrame(viz_frame, text="Zones problématiques détectées", padding=5)
        alerts_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        self.wifi_alert_text = tk.Text(alerts_frame, height=4, wrap=tk.WORD)
        wifi_scroll = ttk.Scrollbar(alerts_frame, command=self.wifi_alert_text.yview)
        self.wifi_alert_text.configure(yscrollcommand=wifi_scroll.set)
        self.wifi_alert_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        wifi_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # === Onglet Moxa ===
        self.moxa_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.moxa_frame, text="Analyse Moxa")

        # Zone de collage des logs
        input_frame = ttk.LabelFrame(self.moxa_frame, text="Collez vos logs Moxa ici :", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.moxa_input = tk.Text(input_frame, wrap=tk.WORD)
        input_scroll = ttk.Scrollbar(input_frame, command=self.moxa_input.yview)
        self.moxa_input.configure(yscrollcommand=input_scroll.set)
        self.moxa_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        input_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Zone d'édition de la configuration courante du Moxa
        config_frame = ttk.LabelFrame(
            self.moxa_frame,
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

        # Boutons de configuration
        config_btn_frame = ttk.Frame(self.moxa_frame)
        config_btn_frame.pack(pady=5)
        ttk.Button(config_btn_frame, text="Charger config", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="Éditer config", command=self.edit_config).pack(side=tk.LEFT, padx=5)

        # Bouton d'analyse
        self.analyze_button = ttk.Button(
            self.moxa_frame,
            text="🔍 Analyser les logs",
            style="Analyze.TButton",
            command=self.analyze_moxa_logs
        )
        self.analyze_button.pack(pady=10)

        # Zone des résultats
        results_frame = ttk.LabelFrame(self.moxa_frame, text="Résultats de l'analyse :", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

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
            tag = simpledialog.askstring(
                "Tag de localisation",
                "Indiquez l'emplacement actuel (ex: usine 1, sous-sol)",
                parent=self.master
            )
            if tag is None:
                return
            if self.analyzer.start_analysis(location_tag=tag.strip()):
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

            # Appel à l'API OpenAI avec la configuration courante
            analysis = analyze_moxa_logs(logs, self.current_config)

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
    """Backward-compatible alias without side effects."""
    pass


def main() -> None:
    """Standalone entry point for manual execution."""
    try:
        root = tk.Tk()
        from bootstrap_ui import BootstrapNetworkAnalyzerUI
        app = BootstrapNetworkAnalyzerUI(root)
        root.mainloop()
    except Exception as exc:  # pragma: no cover - runtime protection
        print(f"Erreur fatale: {exc}")
        tk.messagebox.showerror("Erreur fatale", str(exc))


if __name__ == "__main__":
    main()
