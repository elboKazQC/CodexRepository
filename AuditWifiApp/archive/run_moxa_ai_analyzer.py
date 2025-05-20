# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
from datetime import datetime
from moxa_ai_analyzer import MoxaAIAnalyzer

class MoxaAIAnalyzerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyse IA Moxa")
        self.root.geometry("1200x800")
        
        # Variables pour les paramètres
        self.min_transmission_rate = tk.StringVar(value="6")
        self.max_transmission_power = tk.StringVar(value="20")
        self.rts_threshold = tk.StringVar(value="512")
        self.fragmentation_threshold = tk.StringVar(value="2346")
        self.roaming_mechanism = tk.StringVar(value="signal_strength")
        self.roaming_difference = tk.StringVar(value="9")
        self.remote_connection_check = tk.BooleanVar(value=True)
        self.wmm_enabled = tk.BooleanVar(value=True)
        self.turbo_roaming = tk.BooleanVar(value=True)
        self.ap_alive_check = tk.BooleanVar(value=True)
        
        # Variables pour les nouveaux paramètres de seuil (d'après l'image)
        self.roaming_threshold_type = tk.StringVar(value="signal_strength")
        self.roaming_threshold_value = tk.StringVar(value="-70")  # -70 dBm par défaut
        self.ap_candidate_threshold_type = tk.StringVar(value="signal_strength")
        self.ap_candidate_threshold_value = tk.StringVar(value="-70")  # -70 dBm par défaut
        
        # Chemins de fichiers
        self.log_file_path = tk.StringVar()
        self.results_file_path = tk.StringVar()
        
        # Style pour les widgets
        self.style = ttk.Style()
        self.style.configure("TFrame", padding=5)
        self.style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        self.style.configure("Subheader.TLabel", font=("Arial", 12, "bold"))
        self.style.configure("Bold.TLabel", font=("Arial", 10, "bold"))
        self.style.configure("TNotebook.Tab", padding=[15, 5], font=("Arial", 10))
        self.style.configure("Info.TLabel", foreground="blue")
        self.style.configure("Success.TLabel", foreground="green")
        self.style.configure("Warning.TLabel", foreground="orange")
        self.style.configure("Error.TLabel", foreground="red")
        self.style.configure("Score.TLabel", font=("Arial", 24, "bold"))
        
        # Créer l'analyseur de log IA
        self.analyzer = MoxaAIAnalyzer(api_key=os.environ.get("OPENAI_API_KEY", ""))
        
        # Résultats
        self.analysis_results = None
        
        # Créer l'interface
        self.create_ui()
        
    def create_ui(self):
        # Titre principal
        header_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            header_frame, 
            text="Analyse IA de la Configuration Moxa", 
            style="Header.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        # Créer un cadre principal divisé en deux colonnes
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Colonne gauche (60% de la largeur) - Configuration et Logs
        left_frame = ttk.Frame(main_frame, padding=5)
        main_frame.add(left_frame, weight=60)
        
        # Colonne droite (40% de la largeur) - Analyse et Recommandations
        right_frame = ttk.Frame(main_frame, padding=5)
        main_frame.add(right_frame, weight=40)
        
        # Configuration de l'API et du Moxa (haut gauche)
        self.setup_config_section(left_frame)
        
        # Logs du Moxa (bas gauche)
        self.setup_logs_section(left_frame)
        
        # Analyse et Score (haut droite)
        self.setup_analysis_section(right_frame)
        
        # Recommandations (bas droite)
        self.setup_recommendations_section(right_frame)
        
        # Barre d'état
        self.status_frame = ttk.Frame(self.root, padding=5)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_frame, text="Prêt", anchor="w")
        self.status_label.pack(side=tk.LEFT)
        
        # Version
        version_label = ttk.Label(self.status_frame, text="Version IA 1.0.0")
        version_label.pack(side=tk.RIGHT)
        
    def setup_config_section(self, parent):
        # Frame pour la configuration
        config_frame = ttk.LabelFrame(parent, text="Configuration Moxa", padding=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Section de taux et puissance de transmission
        ttk.Label(config_frame, text="Paramètres de transmission", style="Subheader.TLabel").pack(anchor="w", pady=(0, 10))
        
        # Création d'une grille pour les paramètres
        params_frame = ttk.Frame(config_frame)
        params_frame.pack(fill=tk.X)
        
        # Ligne 1
        ttk.Label(params_frame, text="Taux min:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(params_frame, textvariable=self.min_transmission_rate, width=8).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(params_frame, text="Mbps").grid(row=0, column=2, sticky="w")
        
        ttk.Label(params_frame, text="Puissance max:").grid(row=0, column=3, sticky="e", padx=5, pady=5)
        ttk.Entry(params_frame, textvariable=self.max_transmission_power, width=8).grid(row=0, column=4, sticky="w", padx=5, pady=5)
        ttk.Label(params_frame, text="dBm").grid(row=0, column=5, sticky="w")
        
        # Ligne 2
        ttk.Label(params_frame, text="RTS:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(params_frame, textvariable=self.rts_threshold, width=8).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(params_frame, text="Fragmentation:").grid(row=1, column=3, sticky="e", padx=5, pady=5)
        ttk.Entry(params_frame, textvariable=self.fragmentation_threshold, width=8).grid(row=1, column=4, sticky="w", padx=5, pady=5)
        
        # Séparateur
        ttk.Separator(config_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Section Roaming
        ttk.Label(config_frame, text="Paramètres de Roaming", style="Subheader.TLabel").pack(anchor="w", pady=(0, 10))
        
        roaming_frame = ttk.Frame(config_frame)
        roaming_frame.pack(fill=tk.X)
        
        # Ligne 3 - Mécanisme et Différence
        ttk.Label(roaming_frame, text="Mécanisme:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Combobox(roaming_frame, textvariable=self.roaming_mechanism, values=["signal_strength", "snr"], state="readonly", width=15).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(roaming_frame, text="Différence:").grid(row=0, column=3, sticky="e", padx=5, pady=5)
        ttk.Entry(roaming_frame, textvariable=self.roaming_difference, width=8).grid(row=0, column=4, sticky="w", padx=5, pady=5)
        ttk.Label(roaming_frame, text="dB").grid(row=0, column=5, sticky="w")
        
        # Nouvelle ligne pour le seuil de roaming
        ttk.Label(roaming_frame, text="Type de seuil:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Radiobutton(roaming_frame, text="SNR", variable=self.roaming_threshold_type, value="snr").grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(roaming_frame, text="Signal", variable=self.roaming_threshold_type, value="signal_strength").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        ttk.Label(roaming_frame, text="Seuil de roaming:").grid(row=1, column=3, sticky="e", padx=5, pady=5)
        ttk.Entry(roaming_frame, textvariable=self.roaming_threshold_value, width=8).grid(row=1, column=4, sticky="w", padx=5, pady=5)
        ttk.Label(roaming_frame, text="dBm").grid(row=1, column=5, sticky="w")
        
        # Nouvelle ligne pour le seuil des AP candidats
        ttk.Label(roaming_frame, text="Type candidat:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Radiobutton(roaming_frame, text="SNR", variable=self.ap_candidate_threshold_type, value="snr").grid(row=2, column=1, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(roaming_frame, text="Signal", variable=self.ap_candidate_threshold_type, value="signal_strength").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        
        ttk.Label(roaming_frame, text="Seuil AP candidat:").grid(row=2, column=3, sticky="e", padx=5, pady=5)
        ttk.Entry(roaming_frame, textvariable=self.ap_candidate_threshold_value, width=8).grid(row=2, column=4, sticky="w", padx=5, pady=5)
        ttk.Label(roaming_frame, text="dBm").grid(row=2, column=5, sticky="w")
        
        # Ligne avec checkboxes
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Disposition en grille 2x2 pour les options
        ttk.Label(options_frame, text="Turbo Roaming:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Checkbutton(options_frame, variable=self.turbo_roaming).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(options_frame, text="AP Alive Check:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        ttk.Checkbutton(options_frame, variable=self.ap_alive_check).grid(row=0, column=3, sticky="w", padx=5, pady=5)
        
        ttk.Label(options_frame, text="WMM:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Checkbutton(options_frame, variable=self.wmm_enabled).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(options_frame, text="Remote Check:").grid(row=1, column=2, sticky="e", padx=5, pady=5)
        ttk.Checkbutton(options_frame, variable=self.remote_connection_check).grid(row=1, column=3, sticky="w", padx=5, pady=5)
        
        # Séparateur
        ttk.Separator(config_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Boutons de configuration
        btn_frame = ttk.Frame(config_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Charger config. recommandée", command=self.load_recommended_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Importer config. depuis fichier", command=self.import_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Exporter configuration", command=self.export_config).pack(side=tk.LEFT, padx=5)
    
    def setup_logs_section(self, parent):
        """Section placeholder pour les logs du Moxa (à compléter selon besoins)"""
        logs_frame = ttk.LabelFrame(parent, text="Logs Moxa", padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Ajout d'un widget texte pour afficher les logs (à personnaliser selon besoins)
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=10)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_analysis_section(self, parent):
        """Section pour l'analyse et le score"""
        analysis_frame = ttk.LabelFrame(parent, text="Analyse et Score", padding=10)
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Ajout du bouton pour lancer l'analyse
        analyze_button = ttk.Button(analysis_frame, text="Lancer l'analyse", command=self.run_analysis)
        analyze_button.pack(pady=10)
        
        # Label pour afficher le résultat de l'analyse
        self.analysis_label = ttk.Label(analysis_frame, text="Aucune analyse effectuée.", style="Info.TLabel")
        self.analysis_label.pack(fill=tk.BOTH, expand=True)

    def run_analysis(self):
        """Lance l'analyse des logs Moxa"""
        try:
            # Vérifier la clé API
            if not self.analyzer.api_key.strip():
                messagebox.showerror("Erreur", "Veuillez d'abord configurer votre clé API OpenAI.")
                return

            # Mettre à jour le status
            self.status_label.config(text="Analyse en cours...")
            self.root.update()

            # Collecter la configuration actuelle
            current_config = {
                'min_transmission_rate': int(self.min_transmission_rate.get()),
                'max_transmission_power': int(self.max_transmission_power.get()),
                'rts_threshold': int(self.rts_threshold.get()),
                'fragmentation_threshold': int(self.fragmentation_threshold.get()),
                'roaming_mechanism': self.roaming_mechanism.get(),
                'roaming_difference': int(self.roaming_difference.get()),
                'roaming_threshold_type': self.roaming_threshold_type.get(),
                'roaming_threshold': int(self.roaming_threshold_value.get()),
                'ap_candidate_threshold_type': self.ap_candidate_threshold_type.get(),
                'ap_candidate_threshold': int(self.ap_candidate_threshold_value.get()),
                'remote_connection_check': self.remote_connection_check.get(),
                'wmm_enabled': self.wmm_enabled.get(),
                'turbo_roaming': self.turbo_roaming.get(),
                'ap_alive_check': self.ap_alive_check.get()
            }

            # Lancer l'analyse
            results = self.analyzer.analyze_configuration(current_config)
            self.analysis_results = results

            # Mettre à jour l'interface avec les résultats
            if results:
                # Afficher le score
                score = results.get('score', 0)
                self.analysis_label.config(
                    text=f"Score de configuration: {score}/100",
                    style="Success.TLabel" if score >= 70 else "Warning.TLabel"
                )

                # Afficher les recommandations
                recommendations = results.get('recommendations', {}).get('text', "Aucune recommandation disponible.")
                self.recommendations_label.config(text=recommendations)

                # Sauvegarder les résultats
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                results_file = f"logs_moxa/results_{timestamp}.json"
                os.makedirs("logs_moxa", exist_ok=True)
                with open(results_file, 'w') as f:
                    json.dump(results, f, indent=4)

                self.status_label.config(text="Analyse terminée avec succès.")
            else:
                self.status_label.config(text="Erreur: Aucun résultat d'analyse.")
                messagebox.showerror("Erreur", "L'analyse n'a pas produit de résultats.")

        except Exception as e:
            self.status_label.config(text="Erreur lors de l'analyse.")
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'analyse: {str(e)}")
    
    def setup_recommendations_section(self, parent):
        """Section placeholder for recommendations (to be completed as needed)"""
        recommendations_frame = ttk.LabelFrame(parent, text="Recommandations", padding=10)
        recommendations_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add a label to display recommendations (customize as needed)
        self.recommendations_label = ttk.Label(recommendations_frame, text="Aucune recommandation disponible.", style="Info.TLabel")
        self.recommendations_label.pack(fill=tk.BOTH, expand=True)
    
    def load_recommended_config(self):
        """Charge la configuration recommandée par l'analyse IA"""
        if not self.analysis_results or not 'recommendations' in self.analysis_results:
            messagebox.showwarning("Aucune recommandation", 
                                  "Veuillez d'abord effectuer une analyse pour obtenir des recommandations.")
            return
            
        try:
            # Récupérer les recommandations de l'analyse
            recommendations = self.analysis_results.get('recommendations', {})
            config_recommendations = recommendations.get('configuration', {})
            
            # Mettre à jour les variables de l'interface avec les valeurs recommandées
            if 'min_transmission_rate' in config_recommendations:
                self.min_transmission_rate.set(str(config_recommendations['min_transmission_rate']))
                
            if 'max_transmission_power' in config_recommendations:
                self.max_transmission_power.set(str(config_recommendations['max_transmission_power']))
                
            if 'rts_threshold' in config_recommendations:
                self.rts_threshold.set(str(config_recommendations['rts_threshold']))
                
            if 'fragmentation_threshold' in config_recommendations:
                self.fragmentation_threshold.set(str(config_recommendations['fragmentation_threshold']))
                
            if 'roaming_mechanism' in config_recommendations:
                self.roaming_mechanism.set(config_recommendations['roaming_mechanism'])
                
            if 'roaming_difference' in config_recommendations:
                self.roaming_difference.set(str(config_recommendations['roaming_difference']))
                
            if 'roaming_threshold' in config_recommendations:
                self.roaming_threshold_value.set(str(config_recommendations['roaming_threshold']))
                
            if 'ap_candidate_threshold' in config_recommendations:
                self.ap_candidate_threshold_value.set(str(config_recommendations['ap_candidate_threshold']))
                
            if 'remote_connection_check' in config_recommendations:
                self.remote_connection_check.set(config_recommendations['remote_connection_check'])
                
            if 'wmm_enabled' in config_recommendations:
                self.wmm_enabled.set(config_recommendations['wmm_enabled'])
                
            if 'turbo_roaming' in config_recommendations:
                self.turbo_roaming.set(config_recommendations['turbo_roaming'])
                
            if 'ap_alive_check' in config_recommendations:
                self.ap_alive_check.set(config_recommendations['ap_alive_check'])
                
            messagebox.showinfo("Configuration chargée", 
                              "La configuration recommandée a été chargée avec succès.")
                              
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement de la configuration recommandée: {str(e)}")
            
    def import_config(self):
        """Importe une configuration Moxa depuis un fichier JSON"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier de configuration",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
            initialdir="./config"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
                
            # Mettre à jour les variables de l'interface avec les valeurs du fichier
            if 'min_transmission_rate' in config:
                self.min_transmission_rate.set(str(config['min_transmission_rate']))
                
            if 'max_transmission_power' in config:
                self.max_transmission_power.set(str(config['max_transmission_power']))
                
            if 'rts_threshold' in config:
                self.rts_threshold.set(str(config['rts_threshold']))
                
            if 'fragmentation_threshold' in config:
                self.fragmentation_threshold.set(str(config['fragmentation_threshold']))
                
            if 'roaming_mechanism' in config:
                self.roaming_mechanism.set(config['roaming_mechanism'])
                
            if 'roaming_difference' in config:
                self.roaming_difference.set(str(config['roaming_difference']))
                
            if 'roaming_threshold' in config:
                self.roaming_threshold_value.set(str(config['roaming_threshold']))
                
            if 'ap_candidate_threshold' in config:
                self.ap_candidate_threshold_value.set(str(config['ap_candidate_threshold']))
                
            if 'remote_connection_check' in config:
                self.remote_connection_check.set(config['remote_connection_check'])
                
            if 'wmm_enabled' in config:
                self.wmm_enabled.set(config['wmm_enabled'])
                
            if 'turbo_roaming' in config:
                self.turbo_roaming.set(config['turbo_roaming'])
                
            if 'ap_alive_check' in config:
                self.ap_alive_check.set(config['ap_alive_check'])
                
            messagebox.showinfo("Configuration importée", 
                              f"La configuration a été importée avec succès depuis {os.path.basename(file_path)}.")
                              
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'importation de la configuration: {str(e)}")
            
    def export_config(self):
        """Exporte la configuration actuelle vers un fichier JSON"""
        # Créer un dictionnaire avec la configuration actuelle
        config = {
            'min_transmission_rate': int(self.min_transmission_rate.get()),
            'max_transmission_power': int(self.max_transmission_power.get()),
            'rts_threshold': int(self.rts_threshold.get()),
            'fragmentation_threshold': int(self.fragmentation_threshold.get()),
            'roaming_mechanism': self.roaming_mechanism.get(),
            'roaming_difference': int(self.roaming_difference.get()),
            'roaming_threshold_type': self.roaming_threshold_type.get(),
            'roaming_threshold': int(self.roaming_threshold_value.get()),
            'ap_candidate_threshold_type': self.ap_candidate_threshold_type.get(),
            'ap_candidate_threshold': int(self.ap_candidate_threshold_value.get()),
            'remote_connection_check': self.remote_connection_check.get(),
            'wmm_enabled': self.wmm_enabled.get(),
            'turbo_roaming': self.turbo_roaming.get(),
            'ap_alive_check': self.ap_alive_check.get(),
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
        }
        
        # Créer le dossier config s'il n'existe pas
        os.makedirs("./config", exist_ok=True)
        
        # Déterminer le chemin du fichier de sortie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"moxa_config_{timestamp}.json"
        
        file_path = filedialog.asksaveasfilename(
            title="Enregistrer la configuration",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
            initialdir="./config",
            initialfile=default_filename
        )
        
        if not file_path:
            return
            
        # Ajouter l'extension .json si elle n'est pas présente
        if not file_path.lower().endswith('.json'):
            file_path += '.json'
            
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            messagebox.showinfo("Configuration exportée", 
                              f"La configuration a été exportée avec succès vers {os.path.basename(file_path)}.")
                              
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation de la configuration: {str(e)}")

# Point d'entrée principal
if __name__ == "__main__":
    try:
        # Vérifier les dépendances
        import requests
    except ImportError:
        print("Installation des dépendances requises...")
        
        import subprocess
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
            print("Dépendances installées avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'installation des dépendances: {e}")
            print("Veuillez installer manuellement: pip install requests")
            
            # Attendre une entrée utilisateur avant de quitter
            input("Appuyez sur Entrée pour quitter...")
            sys.exit(1)
    
    print("Lancement de l'interface d'analyse IA Moxa...")
    root = tk.Tk()
    app = MoxaAIAnalyzerUI(root)
    root.mainloop()