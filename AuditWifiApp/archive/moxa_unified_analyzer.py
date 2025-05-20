# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
from datetime import datetime
from moxa_analyzer import MoxaLogAnalyzer

class MoxaUnifiedAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyse Unifiée Moxa")
        self.root.geometry("1200x800")
        
        # Variables pour les paramètres
        self.min_transmission_rate = tk.StringVar(value="6")
        self.max_transmission_power = tk.StringVar(value="20")
        self.rts_threshold = tk.StringVar(value="512")
        self.fragmentation_threshold = tk.StringVar(value="2346")
        self.roaming_mechanism = tk.StringVar(value="signal_strength")
        self.roaming_difference = tk.StringVar(value="9")
        self.roaming_threshold = tk.StringVar(value="-70")  # Ajout du seuil de signal pour roaming
        self.ap_candidate_threshold = tk.StringVar(value="-70")  # Ajout du seuil de signal pour candidat AP
        self.remote_connection_check = tk.BooleanVar(value=True)
        self.wmm_enabled = tk.BooleanVar(value=True)
        self.turbo_roaming = tk.BooleanVar(value=True)
        self.ap_alive_check = tk.BooleanVar(value=True)
        
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
        
        # Créer l'analyseur de log
        self.analyzer = MoxaLogAnalyzer()
        
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
            text="Analyse Unifiée des Configurations Moxa", 
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
        
        # Configuration du Moxa (haut gauche)
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
        version_label = ttk.Label(self.status_frame, text="Version 1.0.0")
        version_label.pack(side=tk.RIGHT)
        
    def setup_config_section(self, parent):
        # Frame pour la configuration
        config_frame = ttk.LabelFrame(parent, text="Configuration Moxa", padding=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Section de taux et puissance de transmission
        ttk.Label(config_frame, text="Paramètres de transmission", style="Subheader.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        
        # Ligne 1
        ttk.Label(config_frame, text="Taux min:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.min_transmission_rate, width=8).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(config_frame, text="Mbps").grid(row=1, column=2, sticky="w")
        
        ttk.Label(config_frame, text="Puissance max:").grid(row=1, column=3, sticky="e", padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.max_transmission_power, width=8).grid(row=1, column=4, sticky="w", padx=5, pady=5)
        ttk.Label(config_frame, text="dBm").grid(row=1, column=5, sticky="w")
        
        # Ligne 2
        ttk.Label(config_frame, text="RTS:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.rts_threshold, width=8).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(config_frame, text="Fragmentation:").grid(row=2, column=3, sticky="e", padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.fragmentation_threshold, width=8).grid(row=2, column=4, sticky="w", padx=5, pady=5)
        
        # Séparateur
        ttk.Separator(config_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=6, sticky="ew", pady=10)
        
        # Section Roaming
        ttk.Label(config_frame, text="Paramètres de Roaming", style="Subheader.TLabel").grid(row=4, column=0, columnspan=4, sticky="w", pady=(0, 10))
        
        # Ligne 3
        ttk.Label(config_frame, text="Mécanisme:").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        ttk.Combobox(config_frame, textvariable=self.roaming_mechanism, values=["signal_strength", "snr"], state="readonly", width=15).grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(config_frame, text="Différence:").grid(row=5, column=3, sticky="e", padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.roaming_difference, width=8).grid(row=5, column=4, sticky="w", padx=5, pady=5)
        ttk.Label(config_frame, text="dB").grid(row=5, column=5, sticky="w")
        
        # Ligne 4 avec seuils
        ttk.Label(config_frame, text="Seuil de signal roaming:").grid(row=6, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.roaming_threshold, width=8).grid(row=6, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(config_frame, text="dBm").grid(row=6, column=2, sticky="w")
        
        ttk.Label(config_frame, text="Seuil candidat AP:").grid(row=6, column=3, sticky="e", padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.ap_candidate_threshold, width=8).grid(row=6, column=4, sticky="w", padx=5, pady=5)
        ttk.Label(config_frame, text="dBm").grid(row=6, column=5, sticky="w")
        
        # Ligne 5 avec checkboxes
        ttk.Label(config_frame, text="Turbo Roaming:").grid(row=7, column=0, sticky="e", padx=5, pady=5)
        ttk.Checkbutton(config_frame, variable=self.turbo_roaming).grid(row=7, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(config_frame, text="AP Alive Check:").grid(row=7, column=3, sticky="e", padx=5, pady=5)
        ttk.Checkbutton(config_frame, variable=self.ap_alive_check).grid(row=7, column=4, sticky="w", padx=5, pady=5)
        
        # Ligne 6 avec checkboxes
        ttk.Label(config_frame, text="WMM:").grid(row=8, column=0, sticky="e", padx=5, pady=5)
        ttk.Checkbutton(config_frame, variable=self.wmm_enabled).grid(row=8, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(config_frame, text="Remote Check:").grid(row=8, column=3, sticky="e", padx=5, pady=5)
        ttk.Checkbutton(config_frame, variable=self.remote_connection_check).grid(row=8, column=4, sticky="w", padx=5, pady=5)
        
        # Séparateur
        ttk.Separator(config_frame, orient=tk.HORIZONTAL).grid(row=9, column=0, columnspan=6, sticky="ew", pady=10)
        
        # Boutons de configuration
        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=10, column=0, columnspan=6, pady=10)
        
        ttk.Button(btn_frame, text="Charger config. recommandée", command=self.load_recommended_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Importer config. depuis fichier", command=self.import_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Exporter configuration", command=self.export_config).pack(side=tk.LEFT, padx=5)
        
        # Configurer le redimensionnement
        for i in range(6):
            config_frame.columnconfigure(i, weight=1)
    
    def setup_logs_section(self, parent):
        # Frame pour les logs
        log_frame = ttk.LabelFrame(parent, text="Logs Moxa", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Section chargement de fichier
        file_frame = ttk.Frame(log_frame)
        file_frame.pack(fill=tk.X)
        
        ttk.Label(file_frame, text="Fichier log:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(file_frame, textvariable=self.log_file_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(file_frame, text="Parcourir...", command=self.browse_log_file).pack(side=tk.LEFT, padx=5)
        
        # Zone de texte pour les logs
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Étiquette pour la zone de texte
        ttk.Label(log_text_frame, text="Contenu du log ou collez le contenu directement:").pack(anchor="w", pady=(0, 5))
        
        # Zone de texte avec barre de défilement
        self.log_text = scrolledtext.ScrolledText(log_text_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Boutons d'action
        btn_frame = ttk.Frame(log_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Créer fichier depuis texte", command=self.create_log_from_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Analyser", command=self.analyze_unified, width=15).pack(side=tk.RIGHT, padx=5)
    
    def setup_analysis_section(self, parent):
        # Frame pour l'analyse et le score
        analysis_frame = ttk.LabelFrame(parent, text="Analyse & Score", padding=10)
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Score et statut
        score_frame = ttk.Frame(analysis_frame)
        score_frame.pack(fill=tk.X, pady=10)
        
        self.score_label = ttk.Label(score_frame, text="--", style="Score.TLabel")
        self.score_label.pack(side=tk.LEFT, padx=20)
        
        self.status_text = ttk.Label(score_frame, text="Non analysé", font=("Arial", 12))
        self.status_text.pack(side=tk.LEFT, padx=10)
        
        # Séparateur
        ttk.Separator(analysis_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Métriques de performance
        metrics_frame = ttk.LabelFrame(analysis_frame, text="Métriques de performance")
        metrics_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Tableau des métriques
        self.metrics_tree = ttk.Treeview(metrics_frame, columns=("value"), show="headings", height=10)
        self.metrics_tree.pack(fill=tk.BOTH, expand=True)
        
        self.metrics_tree.heading("value", text="Valeur")
        self.metrics_tree.column("value", width=100)
        
        # Initialisation avec des valeurs par défaut
        default_metrics = [
            ("Nombre d'événements de roaming", "--"),
            ("Temps de basculement moyen", "--"),
            ("SNR moyen avant roaming", "--"),
            ("SNR moyen après roaming", "--"),
            ("Amélioration SNR", "--"),
            ("Stabilité", "--"),
        ]
        
        for metric, value in default_metrics:
            self.metrics_tree.insert("", tk.END, values=(value,), text=metric)
    
    def setup_recommendations_section(self, parent):
        # Frame pour les recommandations
        recommend_frame = ttk.LabelFrame(parent, text="Recommandations", padding=10)
        recommend_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Liste des recommandations
        self.recommend_list = ttk.Treeview(recommend_frame, columns=("param", "current", "recommended"), show="headings", height=10)
        self.recommend_list.pack(fill=tk.BOTH, expand=True)
        
        self.recommend_list.heading("param", text="Paramètre")
        self.recommend_list.heading("current", text="Valeur actuelle")
        self.recommend_list.heading("recommended", text="Recommandé")
        
        self.recommend_list.column("param", width=120)
        self.recommend_list.column("current", width=100)
        self.recommend_list.column("recommended", width=100)
        
        # Détails de la recommandation sélectionnée
        details_frame = ttk.LabelFrame(recommend_frame, text="Détails")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.recommendation_details = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, height=5)
        self.recommendation_details.pack(fill=tk.BOTH, expand=True)
        self.recommendation_details.insert(tk.END, "Sélectionnez une recommandation pour voir les détails...")
        self.recommendation_details.config(state=tk.DISABLED)
        
        # Événement lors de la sélection
        self.recommend_list.bind("<<TreeviewSelect>>", self.on_recommendation_select)
        
        # Boutons d'action
        btn_frame = ttk.Frame(recommend_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Exporter rapport HTML", command=self.export_html_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Appliquer toutes les recommandations", command=self.apply_all_recommendations).pack(side=tk.RIGHT, padx=5)
    
    def on_recommendation_select(self, event):
        """Affiche les détails de la recommandation sélectionnée"""
        selected_items = self.recommend_list.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        param = self.recommend_list.item(item, "values")[0]
        
        if not self.analysis_results or not self.analysis_results.get('config_changes'):
            return
            
        # Chercher la recommandation correspondante
        for change in self.analysis_results.get('config_changes', []):
            if change.get('param') == param:
                reason = change.get('reason', "Pas d'explication disponible.")
                
                self.recommendation_details.config(state=tk.NORMAL)
                self.recommendation_details.delete(1.0, tk.END)
                self.recommendation_details.insert(tk.END, f"Paramètre: {param}\n\n")
                self.recommendation_details.insert(tk.END, f"Raison: {reason}")
                self.recommendation_details.config(state=tk.DISABLED)
                break
    
    def browse_log_file(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier log"""
        filename = filedialog.askopenfilename(
            title="Sélectionner un fichier log",
            filetypes=(("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*"))
        )
        if filename:
            self.log_file_path.set(filename)
            # Charger le contenu dans la zone de texte
            try:
                with open(filename, 'r', encoding='utf-8-sig', errors='ignore') as file:
                    content = file.read()
                    self.log_text.delete(1.0, tk.END)
                    self.log_text.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la lecture du fichier: {str(e)}")
    
    def create_log_from_text(self):
        """Crée un fichier log temporaire à partir du texte collé"""
        log_text = self.log_text.get("1.0", tk.END).strip()
        if not log_text:
            messagebox.showwarning("Texte vide", "Veuillez coller du contenu dans la zone de texte.")
            return
            
        # Créer un nom de fichier temporaire avec timestamp
        os.makedirs("logs_moxa", exist_ok=True)
        temp_file = os.path.join("logs_moxa", f"temp_log_{self._generate_timestamp()}.txt")
        
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(log_text)
                
            self.log_file_path.set(temp_file)
            messagebox.showinfo("Fichier créé", f"Fichier log temporaire créé: {temp_file}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création du fichier: {str(e)}")
    
    def load_recommended_config(self):
        """Charge la configuration recommandée"""
        self.min_transmission_rate.set("12")
        self.max_transmission_power.set("20") 
        self.rts_threshold.set("512")
        self.fragmentation_threshold.set("2346")
        self.roaming_mechanism.set("snr")
        self.roaming_difference.set("8")
        self.roaming_threshold.set("-65")  # Exemple de valeur recommandée
        self.ap_candidate_threshold.set("-65")  # Exemple de valeur recommandée
        self.remote_connection_check.set(True)
        self.wmm_enabled.set(True)
        self.turbo_roaming.set(True)
        self.ap_alive_check.set(True)
        
        messagebox.showinfo(
            "Configuration chargée", 
            "La configuration recommandée a été chargée. Vous pouvez l'ajuster si nécessaire avant de sauvegarder."
        )
    
    def import_config(self):
        """Importe une configuration depuis un fichier JSON"""
        filename = filedialog.askopenfilename(
            title="Importer une configuration",
            filetypes=(("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")),
            initialdir=os.path.join(os.getcwd(), "config")
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Appliquer les paramètres
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
                    self.roaming_threshold.set(str(config['roaming_threshold']))
                if 'ap_candidate_threshold' in config:
                    self.ap_candidate_threshold.set(str(config['ap_candidate_threshold']))
                if 'remote_connection_check' in config:
                    self.remote_connection_check.set(config['remote_connection_check'])
                if 'wmm_enabled' in config:
                    self.wmm_enabled.set(config['wmm_enabled'])
                if 'turbo_roaming' in config:
                    self.turbo_roaming.set(config['turbo_roaming'])
                if 'ap_alive_check' in config:
                    self.ap_alive_check.set(config['ap_alive_check'])
                
                messagebox.showinfo("Import réussi", f"Configuration importée depuis {os.path.basename(filename)}")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'import: {str(e)}")
    
    def export_config(self):
        """Exporte la configuration actuelle dans un fichier JSON"""
        config = self._get_current_config()
        if not config:
            return
            
        # Demander où sauvegarder
        os.makedirs("config", exist_ok=True)
        filename = filedialog.asksaveasfilename(
            title="Exporter la configuration",
            defaultextension=".json",
            filetypes=(("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")),
            initialdir=os.path.join(os.getcwd(), "config"),
            initialfile=f"moxa_config_{self._generate_timestamp()}.json"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                    
                messagebox.showinfo("Export réussi", f"Configuration exportée vers {os.path.basename(filename)}")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def _get_current_config(self):
        """Récupère la configuration actuelle sous forme de dictionnaire"""
        try:
            config = {
                'min_transmission_rate': int(self.min_transmission_rate.get()),
                'max_transmission_power': int(self.max_transmission_power.get()),
                'rts_threshold': int(self.rts_threshold.get()),
                'fragmentation_threshold': int(self.fragmentation_threshold.get()),
                'roaming_mechanism': self.roaming_mechanism.get(),
                'roaming_difference': int(self.roaming_difference.get()),
                'roaming_threshold': int(self.roaming_threshold.get()),
                'ap_candidate_threshold': int(self.ap_candidate_threshold.get()),
                'remote_connection_check': self.remote_connection_check.get(),
                'wmm_enabled': self.wmm_enabled.get(),
                'turbo_roaming': self.turbo_roaming.get(),
                'ap_alive_check': self.ap_alive_check.get()
            }
            return config
            
        except ValueError as e:
            messagebox.showerror("Erreur de configuration", f"Valeur incorrecte: {str(e)}")
            return None
    
    def analyze_unified(self):
        """Analyse les logs et la configuration de manière unifiée"""
        # Vérifier si un fichier log est spécifié ou créer un fichier à partir du texte
        log_file = self.log_file_path.get()
        
        if not log_file:
            if self.log_text.get("1.0", tk.END).strip():
                # Créer un fichier à partir du texte
                self.create_log_from_text()
                log_file = self.log_file_path.get()
            else:
                messagebox.showerror("Erreur", "Veuillez sélectionner un fichier log ou coller le contenu.")
                return
                
        if not os.path.exists(log_file):
            messagebox.showerror("Erreur", f"Le fichier {log_file} n'existe pas.")
            return
        
        # Récupérer la configuration actuelle
        config = self._get_current_config()
        if not config:
            return
        
        # Préparer le fichier de résultats
        os.makedirs("logs_moxa", exist_ok=True)
        results_file = os.path.join("logs_moxa", f"results_{self._generate_timestamp()}.json")
        
        # Mettre à jour le statut
        self.status_label.config(text="Analyse en cours...")
        self.root.update()
        
        # Créer l'analyseur et définir la configuration actuelle
        self.analyzer = MoxaLogAnalyzer()
        self.analyzer.set_current_config(config)
        
        # Analyser le log
        success = self.analyzer.analyze_log(log_file, results_file)
        
        if success:
            # Stocker les résultats
            self.analysis_results = self.analyzer.results
            
            # Mettre à jour l'interface avec les résultats
            self.update_analysis_display()
            self.update_recommendations_display()
            
            self.status_label.config(text=f"Analyse terminée. Résultats enregistrés dans {results_file}")
        else:
            messagebox.showerror("Erreur d'analyse", "Impossible d'analyser le fichier log.")
            self.status_label.config(text="Erreur lors de l'analyse")
    
    def update_analysis_display(self):
        """Met à jour l'affichage des résultats d'analyse"""
        if not self.analysis_results:
            return
            
        # Mettre à jour le score
        score = self.analysis_results.get('score', 0)
        max_score = self.analysis_results.get('max_score', 100)
        score_percent = int((score / max_score) * 100) if max_score > 0 else 0
        
        self.score_label.config(text=f"{score_percent}%")
        
        if score_percent >= 80:
            self.status_text.config(text="EXCELLENT", foreground="green")
        elif score_percent >= 60:
            self.status_text.config(text="PASSABLE", foreground="orange")
        else:
            self.status_text.config(text="INSUFFISANT", foreground="red")
        
        # Mettre à jour les métriques
        self.metrics_tree.delete(*self.metrics_tree.get_children())
        
        metrics = self.analysis_results.get('roaming_metrics', {})
        
        if metrics:
            self.metrics_tree.insert("", tk.END, values=(metrics.get('total_roaming_events', 0),), text="Nombre d'événements de roaming")
            
            if metrics.get('avg_handoff_time') is not None:
                self.metrics_tree.insert("", tk.END, values=(f"{metrics.get('avg_handoff_time', 0):.1f} ms",), text="Temps de basculement moyen")
            
            if metrics.get('avg_snr_before_roaming') is not None:
                self.metrics_tree.insert("", tk.END, values=(f"{metrics.get('avg_snr_before_roaming', 0):.1f} dB",), text="SNR moyen avant roaming")
            
            if metrics.get('avg_snr_after_roaming') is not None:
                self.metrics_tree.insert("", tk.END, values=(f"{metrics.get('avg_snr_after_roaming', 0):.1f} dB",), text="SNR moyen après roaming")
            
            if metrics.get('snr_improvement') is not None:
                self.metrics_tree.insert("", tk.END, values=(f"{metrics.get('snr_improvement', 0):.1f} dB",), text="Amélioration SNR")
            
            # Calcul de la stabilité
            snr_drop_ratio = metrics.get('roaming_reason_distribution', {}).get('snr_drop', 0) / max(1, metrics.get('total_roaming_events', 1))
            connection_loss_ratio = metrics.get('roaming_reason_distribution', {}).get('connection_loss', 0) / max(1, metrics.get('total_roaming_events', 1))
            stability = f"{(1 - connection_loss_ratio) * 100:.1f}%"
            self.metrics_tree.insert("", tk.END, values=(stability,), text="Stabilité")
    
    def update_recommendations_display(self):
        """Met à jour l'affichage des recommandations"""
        if not self.analysis_results:
            return
            
        # Effacer les recommandations précédentes
        self.recommend_list.delete(*self.recommend_list.get_children())
        
        # Vérifier si nous avons des recommandations à afficher
        if not self.analysis_results.get('config_changes'):
            print("Aucun changement de configuration recommandé n'a été trouvé dans les résultats d'analyse")
            # Ajouter une ligne indiquant qu'aucune recommandation n'a été trouvée
            self.recommend_list.insert("", tk.END, values=("Aucune recommandation", "", ""))
            
            # Afficher un message expliquant pourquoi la configuration est insuffisante
            if self.analysis_results.get('score', 0) < 60:
                self.recommendation_details.config(state=tk.NORMAL)
                self.recommendation_details.delete(1.0, tk.END)
                self.recommendation_details.insert(tk.END, "La configuration actuelle est insuffisante, mais aucune recommandation spécifique n'a été générée.\n\n")
                
                # Ajouter des recommandations génériques basées sur la configuration actuelle
                if self.current_config.get('min_transmission_rate') < 12:
                    self.recommend_list.insert("", tk.END, values=(
                        "Minimum transmission rate", 
                        f"{self.current_config.get('min_transmission_rate')} Mbps", 
                        "12 Mbps"
                    ))
                    
                if self.current_config.get('roaming_mechanism') == 'signal_strength':
                    self.recommend_list.insert("", tk.END, values=(
                        "Roaming threshold", 
                        "Signal Strength", 
                        "SNR"
                    ))
                    
                self.recommendation_details.insert(tk.END, "Recommandations génériques:\n")
                self.recommendation_details.insert(tk.END, "1. Augmenter le taux de transmission minimum à 12 Mbps pour améliorer les performances\n")
                self.recommendation_details.insert(tk.END, "2. Utiliser le mécanisme de roaming basé sur SNR au lieu de force du signal\n")
                self.recommendation_details.insert(tk.END, "3. Activer toutes les options de roaming pour de meilleures performances\n")
                
                self.recommendation_details.config(state=tk.DISABLED)
            return
        
        # Ajouter les nouvelles recommandations
        for change in self.analysis_results.get('config_changes', []):
            param = change.get('param', '')
            current = change.get('current', '')
            recommended = change.get('recommended', '')
            
            self.recommend_list.insert("", tk.END, values=(param, current, recommended))
        
        # Si nous avons au moins une recommandation, sélectionnons-la pour afficher les détails
        if self.recommend_list.get_children():
            first_item = self.recommend_list.get_children()[0]
            self.recommend_list.selection_set(first_item)
            self.on_recommendation_select(None)
    
    def apply_all_recommendations(self):
        """Applique toutes les recommandations à la configuration actuelle"""
        if not self.analysis_results or not self.analysis_results.get('config_changes'):
            messagebox.showinfo("Info", "Aucune recommandation à appliquer.")
            return
            
        changes_applied = 0
        
        for change in self.analysis_results.get('config_changes', []):
            param = change.get('param', '')
            recommended = change.get('recommended', '')
            
            if param == "Minimum transmission rate" and recommended:
                try:
                    value = int(recommended.split()[0])
                    self.min_transmission_rate.set(str(value))
                    changes_applied += 1
                except:
                    pass
            elif param == "Maximum transmission power" and recommended:
                try:
                    value = int(recommended.split()[0])
                    self.max_transmission_power.set(str(value))
                    changes_applied += 1
                except:
                    pass
            elif param == "RTS threshold" and recommended:
                try:
                    self.rts_threshold.set(recommended)
                    changes_applied += 1
                except:
                    pass
            elif param == "Fragmentation threshold" and recommended:
                try:
                    self.fragmentation_threshold.set(recommended)
                    changes_applied += 1
                except:
                    pass
            elif param == "Roaming threshold" and recommended:
                if recommended.lower() == "snr":
                    self.roaming_mechanism.set("snr")
                    changes_applied += 1
                elif recommended.lower() == "signal strength":
                    self.roaming_mechanism.set("signal_strength")
                    changes_applied += 1
            elif param == "Roaming difference" and recommended:
                try:
                    value = int(recommended.split()[0])
                    self.roaming_difference.set(str(value))
                    changes_applied += 1
                except:
                    pass
            elif param == "Roaming signal threshold" and recommended:
                try:
                    value = int(recommended.split()[0])
                    self.roaming_threshold.set(str(value))
                    changes_applied += 1
                except:
                    pass
            elif param == "AP candidate signal threshold" and recommended:
                try:
                    value = int(recommended.split()[0])
                    self.ap_candidate_threshold.set(str(value))
                    changes_applied += 1
                except:
                    pass
            elif param == "Remote connection check" and recommended.lower() == "enabled":
                self.remote_connection_check.set(True)
                changes_applied += 1
            elif param == "WMM" and recommended.lower() == "enabled":
                self.wmm_enabled.set(True)
                changes_applied += 1
            elif param == "Turbo Roaming" and recommended.lower() == "enabled":
                self.turbo_roaming.set(True)
                changes_applied += 1
            elif param == "AP alive check" and recommended.lower() == "enabled":
                self.ap_alive_check.set(True)
                changes_applied += 1
        
        if changes_applied > 0:
            messagebox.showinfo("Recommandations appliquées", f"{changes_applied} changements ont été appliqués à la configuration.")
            
            # Proposer de relancer l'analyse
            if messagebox.askyesno("Relancer l'analyse", "Voulez-vous relancer l'analyse avec la nouvelle configuration?"):
                self.analyze_unified()
        else:
            messagebox.showinfo("Info", "Aucun changement n'a pu être appliqué.")
    
    def export_html_report(self):
        """Exporte un rapport HTML complet"""
        if not self.analysis_results:
            messagebox.showwarning("Aucun résultat", "Veuillez d'abord analyser un log.")
            return
            
        # Demander où sauvegarder
        filename = filedialog.asksaveasfilename(
            title="Exporter le rapport HTML",
            defaultextension=".html",
            filetypes=(("Fichiers HTML", "*.html"), ("Tous les fichiers", "*.*"))
        )
        
        if not filename:
            return
            
        try:
            # Générer le rapport HTML
            html = self._generate_html_report()
            
            # Sauvegarder
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
                
            messagebox.showinfo("Export réussi", f"Rapport HTML exporté vers {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export HTML: {str(e)}")
    
    def _generate_html_report(self):
        """Génère un rapport HTML à partir des résultats d'analyse"""
        results = self.analysis_results
        metrics = results.get('roaming_metrics', {})
        
        # Calcul du score en pourcentage
        score_percent = int((results['score'] / results['max_score']) * 100) if results.get('max_score', 0) > 0 else 0
        score_class = "excellent" if score_percent >= 80 else "good" if score_percent >= 60 else "poor"
        
        # Configuration actuelle
        config = self._get_current_config()
        
        # Créer le HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rapport d'analyse Moxa Unifié</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3 {{
                    color: #0066cc;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                }}
                .score-box {{
                    text-align: center;
                    margin: 20px 0;
                    padding: 15px;
                    border-radius: 5px;
                }}
                .excellent {{
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                }}
                .good {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeeba;
                    color: #856404;
                }}
                .poor {{
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 12px 15px;
                    border: 1px solid #ddd;
                    text-align: left;
                }}
                th {{
                    background-color: #f8f9fa;
                }}
                .recommendation {{
                    background-color: #e2f0fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .content-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    font-size: 0.8em;
                    color: #666;
                }}
                .parameter-ok {{
                    color: green;
                }}
                .parameter-warning {{
                    color: orange;
                }}
                .parameter-error {{
                    color: red;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Rapport d'analyse Moxa Unifié</h1>
                <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            </div>
            
            <div class="score-box {score_class}">
                <h2>Score global: {score_percent}%</h2>
                <p>{results.get('score', 0)} points sur un maximum de {results.get('max_score', 100)}</p>
                <p><strong>Statut: {"EXCELLENT" if score_percent >= 80 else "PASSABLE" if score_percent >= 60 else "INSUFFISANT"}</strong></p>
            </div>
            
            <div class="content-grid">
                <div>
                    <h2>Configuration Moxa</h2>
                    <table>
                        <tr>
                            <th colspan="2">Paramètres de transmission</th>
                        </tr>
                        <tr>
                            <td>Taux de transmission min</td>
                            <td>{config.get('min_transmission_rate', '--')} Mbps</td>
                        </tr>
                        <tr>
                            <td>Puissance de transmission max</td>
                            <td>{config.get('max_transmission_power', '--')} dBm</td>
                        </tr>
                        <tr>
                            <td>Seuil RTS</td>
                            <td>{config.get('rts_threshold', '--')}</td>
                        </tr>
                        <tr>
                            <td>Seuil de fragmentation</td>
                            <td>{config.get('fragmentation_threshold', '--')}</td>
                        </tr>
                        <tr>
                            <th colspan="2">Paramètres de Roaming</th>
                        </tr>
                        <tr>
                            <td>Mécanisme de roaming</td>
                            <td>{config.get('roaming_mechanism', '--')}</td>
                        </tr>
                        <tr>
                            <td>Différence de roaming</td>
                            <td>{config.get('roaming_difference', '--')} dB</td>
                        </tr>
                        <tr>
                            <td>Seuil de signal roaming</td>
                            <td>{config.get('roaming_threshold', '--')} dBm</td>
                        </tr>
                        <tr>
                            <td>Seuil candidat AP</td>
                            <td>{config.get('ap_candidate_threshold', '--')} dBm</td>
                        </tr>
                        <tr>
                            <td>Turbo Roaming</td>
                            <td>{"Activé" if config.get('turbo_roaming', False) else "Désactivé"}</td>
                        </tr>
                        <tr>
                            <td>AP alive check</td>
                            <td>{"Activé" if config.get('ap_alive_check', False) else "Désactivé"}</td>
                        </tr>
                        <tr>
                            <td>WMM</td>
                            <td>{"Activé" if config.get('wmm_enabled', False) else "Désactivé"}</td>
                        </tr>
                        <tr>
                            <td>Remote connection check</td>
                            <td>{"Activé" if config.get('remote_connection_check', False) else "Désactivé"}</td>
                        </tr>
                    </table>
        """
        
        # Ajouter les métriques de roaming
        if metrics:
            html += """
                    <h2>Métriques de Roaming</h2>
                    <table>
                        <tr>
                            <th>Métrique</th>
                            <th>Valeur</th>
                        </tr>
            """
            
            html += f"""
                        <tr><td>Événements de roaming</td><td>{metrics.get('total_roaming_events', 0)}</td></tr>
            """
            
            if metrics.get('avg_handoff_time') is not None:
                html += f"""
                        <tr><td>Temps de basculement moyen</td><td>{metrics.get('avg_handoff_time', 0):.1f} ms</td></tr>
                        <tr><td>Temps de basculement min/max</td><td>{metrics.get('min_handoff_time', 0)} ms / {metrics.get('max_handoff_time', 0)} ms</td></tr>
                """
            
            if metrics.get('avg_snr_before_roaming') is not None:
                html += f"""
                        <tr><td>SNR moyen avant roaming</td><td>{metrics.get('avg_snr_before_roaming', 0):.1f} dB</td></tr>
                """
            
            if metrics.get('avg_snr_after_roaming') is not None:
                html += f"""
                        <tr><td>SNR moyen après roaming</td><td>{metrics.get('avg_snr_after_roaming', 0):.1f} dB</td></tr>
                """
            
            if metrics.get('snr_improvement') is not None:
                html += f"""
                        <tr><td>Amélioration SNR moyenne</td><td>{metrics.get('snr_improvement', 0):.1f} dB</td></tr>
                """
            
            if metrics.get('avg_association_time') is not None:
                assoc_seconds = metrics.get('avg_association_time', 0) / 1000
                html += f"""
                        <tr><td>Temps d'association moyen</td><td>{assoc_seconds:.1f} s</td></tr>
                """
            
            html += """
                    </table>
                    
                    <h3>Raisons de roaming</h3>
                    <table>
                        <tr>
                            <th>Raison</th>
                            <th>Nombre</th>
                            <th>Pourcentage</th>
                        </tr>
            """
            
            for reason, count in metrics.get('roaming_reason_distribution', {}).items():
                perc = (count / metrics.get('total_roaming_events', 1)) * 100 if metrics.get('total_roaming_events', 0) > 0 else 0
                reason_str = "Baisse de SNR" if reason == "snr_drop" else "Perte de connexion" if reason == "connection_loss" else "Inconnue"
                
                html += f"""
                        <tr>
                            <td>{reason_str}</td>
                            <td>{count}</td>
                            <td>{perc:.1f}%</td>
                        </tr>
                """
            
            html += """
                    </table>
            """
        
        html += """
                </div>
                <div>
        """
        
        # Ajouter les détails des paramètres
        if results.get('details'):
            html += """
                    <h2>Paramètres analysés</h2>
                    <table>
                        <tr>
                            <th>Paramètre</th>
                            <th>Valeur</th>
                            <th>Idéal</th>
                            <th>Score</th>
                            <th>Statut</th>
                        </tr>
            """
            
            for param_name, details in results['details'].items():
                status_class = f"parameter-{details.get('status', 'warning')}"
                status_icon = "✅" if details.get('status') == "ok" else "⚠️" if details.get('status') == "warning" else "❌"
                
                # Formatage pour l'affichage
                if param_name == 'handoff_time':
                    param_display = "Temps de basculement"
                    value_display = f"{details.get('value', 0):.1f} ms"
                elif param_name == 'snr_improvement':
                    param_display = "Amélioration SNR"
                    value_display = f"{details.get('value', 0):.1f} dB"
                elif param_name == 'roaming_stability':
                    param_display = "Stabilité roaming"
                    value_display = details.get('value', "N/A")
                elif isinstance(details.get('value'), bool):
                    param_display = param_name.replace('_', ' ').title()
                    value_display = "Activé" if details.get('value') else "Désactivé"
                else:
                    param_display = param_name.replace('_', ' ').title()
                    value_display = str(details.get('value', "N/A"))
                
                ideal_value = str(details.get('ideal_value', "N/A")) if 'ideal_value' in details else "N/A"
                
                html += f"""
                        <tr>
                            <td>{param_display}</td>
                            <td>{value_display}</td>
                            <td>{ideal_value}</td>
                            <td>{details.get('score', 0):.1f}/{details.get('max_score', 0)}</td>
                            <td class="{status_class}">{status_icon}</td>
                        </tr>
                """
            
            html += """
                    </table>
            """
        
        # Ajouter les recommandations
        if results.get('recommendations'):
            html += """
                    <div class="recommendation">
                        <h2>Recommandations</h2>
                        <ul>
            """
            
            for rec in results.get('recommendations', []):
                html += f"            <li>{rec}</li>\n"
            
            html += """
                        </ul>
                    </div>
            """
        
        # Ajouter les changements de configuration recommandés
        if results.get('config_changes'):
            html += """
                    <h2>Changements de configuration recommandés</h2>
                    <table>
                        <tr>
                            <th>Paramètre</th>
                            <th>Valeur actuelle</th>
                            <th>Valeur recommandée</th>
                            <th>Raison</th>
                        </tr>
            """
            
            for change in results.get('config_changes', []):
                html += f"""
                        <tr>
                            <td>{change.get('param', '')}</td>
                            <td>{change.get('current', '')}</td>
                            <td><strong>{change.get('recommended', '')}</strong></td>
                            <td>{change.get('reason', '')}</td>
                        </tr>
                """
            
            html += """
                    </table>
            """
        
        # Fermer les divs et ajouter le pied de page
        html += """
                </div>
            </div>
            
            <div class="footer">
                <p>Rapport unifié généré par AuditWifiApp - Optimiseur de configuration Moxa</p>
                <p>© 2025 Noovelia</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_timestamp(self):
        """Génère un timestamp pour les noms de fichiers"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

# Ajout d'un point d'entrée pour exécuter directement ce fichier
if __name__ == "__main__":
    print("Lancement de l'interface d'analyse unifiée Moxa...")
    root = tk.Tk()
    app = MoxaUnifiedAnalyzer(root)
    print("Interface Moxa chargée avec succès. En attente d'actions utilisateur...")
    root.mainloop()