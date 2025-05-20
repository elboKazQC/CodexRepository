# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import re
import time
import os
import csv
from audit_steps import AuditManager
from moxa_analyzer import MoxaLogAnalyzer

class AuditWifiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audit Wifi App")
        self.geometry("500x900")  # Augmenté pour les étapes d'audit
        self.resizable(False, False)
        self.status = "Inconnu"
        self.is_recording = False
        
        # Gestionnaire d'audit
        self.audit_manager = AuditManager()
        
        # Créer le dossier logs s'il n'existe pas
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Nom du fichier de log basé sur la date
        self.log_file = f'logs/audit_{time.strftime("%Y-%m-%d")}.csv'
        
        # Créer le fichier CSV avec les en-têtes s'il n'existe pas ou vérifier sa structure
        self.check_and_create_log_file()
        
        self.create_widgets()
        self.update_network_data()
        
    def check_and_create_log_file(self):
        """Vérifie et crée le fichier de log si nécessaire"""
        headers = ['Timestamp', 'Type', 'Signal_%', 'RSSI_dBm', 'SSID', 'BSSID', 
                  'Band', 'Channel', 'Radio_Type', 'RX_Speed', 'TX_Speed', 'Ping', 'Description']
        
        if not os.path.exists(self.log_file):
            # Créer un nouveau fichier avec les en-têtes
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            print(f"Nouveau fichier CSV créé: {self.log_file}")
        else:
            # Vérifier si le fichier a la bonne structure
            try:
                with open(self.log_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    existing_headers = next(reader, None)
                print(f"En-têtes existants: {existing_headers}")
                
                # Si les en-têtes ne correspondent pas, renommer l'ancien fichier et en créer un nouveau
                if not existing_headers or 'RSSI_dBm' not in existing_headers:
                    backup_file = f"{self.log_file}.bak"
                    print(f"Structure CSV invalide, sauvegarde vers {backup_file}")
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                    os.rename(self.log_file, backup_file)
                    
                    # Créer un nouveau fichier avec les en-têtes corrects
                    with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                    print(f"Nouveau fichier CSV créé avec la structure correcte")
            except Exception as e:
                print(f"Erreur lors de la vérification du fichier CSV: {e}")
                # Renommer l'ancien fichier et en créer un nouveau
                backup_file = f"{self.log_file}.bak"
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rename(self.log_file, backup_file)
                
                # Créer un nouveau fichier avec les en-têtes corrects
                with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                print(f"Nouveau fichier CSV créé après erreur de lecture")

    def create_widgets(self):
        # Zone Signal WiFi
        frame_base = ttk.LabelFrame(self, text="Signal WiFi")
        frame_base.pack(fill="x", padx=10, pady=5)
        
        self.label_signal = ttk.Label(frame_base, text="Signal: -- %", font=("Arial", 14))
        self.label_signal.pack(pady=5, padx=10, anchor="w")
        
        self.label_rssi = ttk.Label(frame_base, text="RSSI: -- dBm", font=("Arial", 14))
        self.label_rssi.pack(pady=5, padx=10, anchor="w")
        
        self.label_ping = ttk.Label(frame_base, text="Ping: -- ms", font=("Arial", 14))
        self.label_ping.pack(pady=5, padx=10, anchor="w")
        
        # Zone Détails
        frame_details = ttk.LabelFrame(self, text="Détails du réseau")
        frame_details.pack(fill="x", padx=10, pady=5)
        
        self.label_ssid = ttk.Label(frame_details, text="SSID: --", font=("Arial", 12))
        self.label_ssid.pack(pady=2, padx=10, anchor="w")
        
        self.label_bssid = ttk.Label(frame_details, text="Point d'accès: --", font=("Arial", 12))
        self.label_bssid.pack(pady=2, padx=10, anchor="w")
        
        self.label_band = ttk.Label(frame_details, text="Bande: --", font=("Arial", 12))
        self.label_band.pack(pady=2, padx=10, anchor="w")
        
        self.label_channel = ttk.Label(frame_details, text="Canal: --", font=("Arial", 12))
        self.label_channel.pack(pady=2, padx=10, anchor="w")
        
        self.label_radio = ttk.Label(frame_details, text="Type de radio: --", font=("Arial", 12))
        self.label_radio.pack(pady=2, padx=10, anchor="w")
        
        self.label_speed = ttk.Label(frame_details, text="Débit: -- / -- Mbps", font=("Arial", 12))
        self.label_speed.pack(pady=2, padx=10, anchor="w")
        
        # Zone Boutons
        frame_buttons = ttk.Frame(self)
        frame_buttons.pack(fill="x", padx=10, pady=15)
        
        self.btn_explain = ttk.Button(frame_buttons, text="Analyser qualité du signal", command=self.show_signal_quality)
        self.btn_explain.pack(pady=5, fill="x")
        
        # Zone Audit
        frame_audit = ttk.LabelFrame(self, text="Audit WiFi")
        frame_audit.pack(fill="x", padx=10, pady=5)
        
        # Bouton Démarrer/Arrêter l'enregistrement
        self.record_button = ttk.Button(frame_audit, text="▶ Démarrer l'enregistrement", 
                                      command=self.toggle_recording)
        self.record_button.pack(pady=5, fill="x", padx=10)
        
        # Bouton Marquer position
        self.mark_button = ttk.Button(frame_audit, text="📍 Marquer position", 
                                    command=self.mark_position)
        self.mark_button.pack(pady=5, fill="x", padx=10)
        
        # Zone Description
        self.description_var = tk.StringVar()
        description_frame = ttk.Frame(frame_audit)
        description_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(description_frame, text="Description:").pack(side="left")
        self.description_entry = ttk.Entry(description_frame, textvariable=self.description_var)
        self.description_entry.pack(side="left", fill="x", expand=True, padx=(5,0))
        
        # Zone Étapes d'audit
        frame_steps = ttk.LabelFrame(self, text="Étapes d'audit")
        frame_steps.pack(fill="x", padx=10, pady=5)
        
        # Progression des étapes
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(frame_steps, variable=self.progress_var, 
                                          maximum=3, length=200, mode='determinate')
        self.progress_bar.pack(pady=5, padx=10, fill="x")
        
        # État de l'étape courante
        self.step_label = ttk.Label(frame_steps, text="Étape 1: Tour de l'usine", 
                                  font=("Arial", 12, "bold"))
        self.step_label.pack(pady=5, padx=10)
        
        self.step_description = ttk.Label(frame_steps, 
                                        text="Faites le tour de l'usine en enregistrant les points faibles",
                                        wraplength=400)
        self.step_description.pack(pady=5, padx=10)
        
        # Boutons de contrôle des étapes
        step_buttons = ttk.Frame(frame_steps)
        step_buttons.pack(fill="x", padx=10, pady=5)
        
        self.start_step_btn = ttk.Button(step_buttons, text="▶ Démarrer étape", 
                                       command=self.start_current_step)
        self.start_step_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        self.complete_step_btn = ttk.Button(step_buttons, text="✓ Terminer étape", 
                                          command=self.complete_current_step)
        self.complete_step_btn.pack(side="right", padx=5, fill="x", expand=True)
        
        # Zone État
        self.status_frame = ttk.LabelFrame(self, text="État")
        self.status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Prêt", font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        self.timestamp_label = ttk.Label(self, text="Dernière mise à jour: --", font=("Arial", 8))
        self.timestamp_label.pack(side="bottom", pady=5)

    def get_network_data(self):
        data = {
            'signal_percent': 0,
            'rssi': 0,
            'ping': 0,
            'ssid': "Inconnu",
            'bssid': "Inconnu",
            'band': "Inconnu",
            'channel': "Inconnu",
            'radio_type': "Inconnu",
            'rx_speed': 0,
            'tx_speed': 0
        }
        
        try:
            output = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], encoding='utf-8-sig', errors='ignore')
            for line in output.split('\n'):
                line = line.strip()
                if 'Signal' in line:
                    match = re.search(r'Signal\s*:\s*(\d+)%', line)
                    if match:
                        data['signal_percent'] = int(match.group(1))
                        data['rssi'] = int((data['signal_percent'] / 2) - 100)
                elif 'SSID' in line and not any(x in line.lower() for x in ['identificateur', 'identifier']):
                    match = re.search(r'SSID\s*:\s*(.+)', line)
                    if match:
                        data['ssid'] = match.group(1).strip()
                elif "identificateur SSID" in line or "SSID identifier" in line:
                    match = re.search(r':\s*([0-9A-Fa-f:]+)', line)
                    if match:
                        data['bssid'] = match.group(1).strip()
                elif 'Bande' in line:
                    match = re.search(r'Bande\s*:\s*(.+)', line)
                    if match:
                        data['band'] = match.group(1).strip()
                elif 'Canal' in line:
                    match = re.search(r'Canal\s*:\s*(.+)', line)
                    if match:
                        data['channel'] = match.group(1).strip()
                elif 'Type de radio' in line:
                    match = re.search(r'Type de radio\s*:\s*(.+)', line)
                    if match:
                        data['radio_type'] = match.group(1).strip()
                elif 'Réception' in line:
                    match = re.search(r'Réception.*:\s*(\d+)', line)
                    if match:
                        data['rx_speed'] = int(match.group(1))
                elif 'Transmission' in line:
                    match = re.search(r'Transmission.*:\s*(\d+)', line)
                    if match:
                        data['tx_speed'] = int(match.group(1))
                        
            # Si on n'a toujours pas trouvé le BSSID, essayons une recherche plus large
            if data['bssid'] == "Inconnu":
                for line in output.split('\n'):
                    if re.search(r'[0-9A-Fa-f:]{17}', line):
                        match = re.search(r'([0-9A-Fa-f:]{17})', line)
                        if match:
                            data['bssid'] = match.group(1).strip()
                            break
        except Exception as e:
            self.status_label.config(text=f"Erreur WiFi: {str(e)}")
        
        try:
            ping_output = subprocess.check_output(['ping', '-n', '1', '8.8.8.8'], encoding='utf-8-sig', errors='ignore')
            ping_match = re.search(r'Moyenne = (\d+)ms', ping_output)
            if not ping_match:
                ping_match = re.search(r'Average = (\d+)ms', ping_output)
            if ping_match:
                data['ping'] = int(ping_match.group(1))
        except Exception as e:
            self.status_label.config(text=f"Erreur ping: {str(e)}")
        
        return data

    def log_data(self, log_type, description=""):
        """Enregistre les données dans le fichier CSV"""
        data = self.get_network_data()
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                current_time,
                log_type,
                data['signal_percent'],
                data['rssi'],
                data['ssid'],
                data['bssid'],
                data['band'],
                data['channel'],
                data['radio_type'],
                data['rx_speed'],
                data['tx_speed'],
                data['ping'],
                description
            ])
            
        # Afficher un message de confirmation
        self.status_label.config(text=f"Position enregistrée: {description}" if description else "Données enregistrées")

    def toggle_recording(self):
        """Démarre ou arrête l'enregistrement automatique"""
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.record_button.config(text="⏹ Arrêter l'enregistrement")
            self.status_label.config(text="Enregistrement automatique activé")
        else:
            self.record_button.config(text="▶ Démarrer l'enregistrement")
            self.status_label.config(text="Enregistrement automatique désactivé")

    def mark_position(self):
        """Enregistre manuellement la position actuelle avec description"""
        description = self.description_var.get().strip()
        if not description:
            messagebox.showwarning("Description manquante", 
                                 "Veuillez entrer une description de l'emplacement")
            return
            
        self.log_data("MANUAL", description)
        self.description_var.set("")  # Effacer la description après l'enregistrement

    def start_current_step(self):
        """Démarre l'étape courante de l'audit"""
        current_step = self.audit_manager.get_current_step()
        if current_step:
            if current_step.name == "Tour de l'usine":
                if not self.is_recording:
                    self.toggle_recording()  # Démarre l'enregistrement
            self.audit_manager.start_step()
            self.update_step_display()
            messagebox.showinfo("Étape démarrée", 
                              f"L'étape '{current_step.name}' a démarré.\n\n{current_step.description}")

    def complete_current_step(self):
        """Termine l'étape courante de l'audit"""
        current_step = self.audit_manager.get_current_step()
        if current_step:
            if current_step.name == "Tour de l'usine":
                if self.is_recording:
                    self.toggle_recording()  # Arrête l'enregistrement
                
                # Analyse des données collectées
                try:
                    with open(self.log_file, 'r') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        # Vérifier si le CSV a la structure attendue
                        if rows and 'RSSI_dBm' in rows[0]:
                            weak_spots = sum(1 for row in rows if int(row['RSSI_dBm']) < -75)
                        else:
                            # Gérer le cas où la structure est différente
                            print(f"Structure CSV inattendue. Colonnes: {rows[0].keys() if rows else 'aucune donnée'}")
                            weak_spots = 0
                        
                    success = weak_spots <= 3  # Critère: pas plus de 3 points faibles
                    self.audit_manager.complete_step(success, {
                        "points_collected": len(rows) if rows else 0,
                        "weak_spots": weak_spots
                    })
                    
                    if not success:
                        messagebox.showwarning("Étape échouée", 
                                             f"Trop de points faibles détectés ({weak_spots} > 3).\n"
                                             "Vous devriez refaire un tour en évitant les zones problématiques.")
                        return
                except Exception as e:
                    print(f"Erreur lors de l'analyse des données: {e}")
                    messagebox.showerror("Erreur", f"Erreur lors de l'analyse des données: {e}")
                    return
                    
            elif current_step.name == "Analyse Moxa":
                # Vérifier si un fichier log a été analysé
                if not hasattr(self, 'moxa_analysis_results') or not self.moxa_analysis_results:
                    messagebox.showwarning("Aucune analyse", 
                                         "Vous devez d'abord analyser un fichier log Moxa.")
                    return
                
                # Vérifier si l'analyse a passé le seuil
                passed = self.moxa_analysis_results.get('passed', False)
                score = self.moxa_analysis_results.get('score', 0)
                
                # Compléter l'étape avec le succès ou l'échec
                self.audit_manager.complete_step(passed, {
                    "score": score,
                    "passed": passed,
                    "recommendations": self.moxa_analysis_results.get('recommendations', [])
                })
                
                if not passed:
                    messagebox.showwarning("Étape échouée", 
                                         f"Le score d'analyse Moxa ({score}/100) est inférieur au seuil requis (70/100).\n"
                                         "Veuillez ajuster les paramètres Moxa selon les recommandations et réessayer.")
                    return
                
            elif current_step.name == "Rapport final":
                try:
                    report = self.audit_manager.generate_report()
                    messagebox.showinfo("Rapport généré", 
                                      f"Le rapport a été sauvegardé dans logs/audit_report_{time.strftime('%Y-%m-%d')}.json")
                except Exception as e:
                    print(f"Erreur lors de la génération du rapport: {e}")
                    messagebox.showerror("Erreur", f"Erreur lors de la génération du rapport: {e}")
                    return
            
            self.progress_var.set(self.audit_manager.current_step)
            self.update_step_display()

    def update_step_display(self):
        """Met à jour l'affichage de l'étape courante"""
        current_step = self.audit_manager.get_current_step()
        if current_step:
            self.step_label.config(text=f"Étape {self.audit_manager.current_step + 1}: {current_step.name}")
            self.step_description.config(text=current_step.description)
            
            # Activer/désactiver les boutons selon l'état
            self.start_step_btn.config(state="normal" if not current_step.start_time else "disabled")
            self.complete_step_btn.config(state="normal" if current_step.start_time else "disabled")
            
            # Afficher/masquer l'interface Moxa selon l'étape
            if current_step.name == "Analyse Moxa" and current_step.start_time:
                self.show_moxa_interface()
            else:
                self.hide_moxa_interface()
        else:
            self.step_label.config(text="Audit terminé")
            self.step_description.config(text="Toutes les étapes sont terminées")
            self.start_step_btn.config(state="disabled")
            self.complete_step_btn.config(state="disabled")
            self.hide_moxa_interface()
    
    def show_moxa_interface(self):
        """Affiche l'interface d'analyse des logs Moxa"""
        if not hasattr(self, 'moxa_frame'):
            # Créer le cadre pour l'analyse Moxa s'il n'existe pas
            self.moxa_frame = ttk.LabelFrame(self, text="Analyse des logs Moxa")
            self.moxa_frame.pack(fill="x", padx=10, pady=5)
            
            # Bouton pour sélectionner un fichier log
            select_frame = ttk.Frame(self.moxa_frame)
            select_frame.pack(fill="x", padx=10, pady=5)
            
            self.moxa_log_path_var = tk.StringVar()
            self.moxa_log_entry = ttk.Entry(select_frame, textvariable=self.moxa_log_path_var, state="readonly")
            self.moxa_log_entry.pack(side="left", fill="x", expand=True)
            
            select_btn = ttk.Button(select_frame, text="Parcourir...", command=self.select_moxa_log)
            select_btn.pack(side="right", padx=(5, 0))
            
            # Bouton d'analyse
            analyze_btn = ttk.Button(self.moxa_frame, text="Analyser le log", command=self.analyze_moxa_log)
            analyze_btn.pack(fill="x", padx=10, pady=5)
            
            # Zone de résultats
            self.moxa_result_text = tk.Text(self.moxa_frame, height=10, width=50, wrap="word")
            self.moxa_result_text.pack(fill="both", expand=True, padx=10, pady=5)
            self.moxa_result_text.config(state="disabled")
            
            # Barre de défilement
            scrollbar = ttk.Scrollbar(self.moxa_result_text, command=self.moxa_result_text.yview)
            scrollbar.pack(side="right", fill="y")
            self.moxa_result_text.config(yscrollcommand=scrollbar.set)
        else:
            # Afficher le cadre s'il existe déjà
            self.moxa_frame.pack(fill="x", padx=10, pady=5)
    
    def hide_moxa_interface(self):
        """Masque l'interface d'analyse des logs Moxa"""
        if hasattr(self, 'moxa_frame'):
            self.moxa_frame.pack_forget()
    
    def select_moxa_log(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier log Moxa"""
        filepath = filedialog.askopenfilename(
            title="Sélectionner un fichier log Moxa",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
            initialdir=os.path.join(os.getcwd(), "logs_moxa")
        )
        
        if filepath:
            self.moxa_log_path_var.set(filepath)
            # Réinitialiser les résultats précédents
            self.moxa_analysis_results = None
            self.moxa_result_text.config(state="normal")
            self.moxa_result_text.delete(1.0, tk.END)
            self.moxa_result_text.insert(tk.END, "Fichier sélectionné. Cliquez sur 'Analyser le log' pour continuer.")
            self.moxa_result_text.config(state="disabled")
    
    def analyze_moxa_log(self):
        """Analyse le fichier log Moxa sélectionné"""
        filepath = self.moxa_log_path_var.get()
        if not filepath:
            messagebox.showwarning("Aucun fichier", "Veuillez d'abord sélectionner un fichier log Moxa.")
            return
        
        # Créer le dossier logs_moxa s'il n'existe pas
        if not os.path.exists('logs_moxa'):
            os.makedirs('logs_moxa')
        
        # Analyser le log
        analyzer = MoxaLogAnalyzer()
        success = analyzer.analyze_log(
            filepath, 
            os.path.join('logs_moxa', f'analysis_{time.strftime("%Y-%m-%d")}.json')
        )
        
        if not success:
            messagebox.showerror("Erreur d'analyse", "Impossible d'analyser le fichier log Moxa.")
            return
        
        # Afficher les résultats
        self.moxa_analysis_results = analyzer.results
        friendly_report = analyzer.get_user_friendly_report()
        
        self.moxa_result_text.config(state="normal")
        self.moxa_result_text.delete(1.0, tk.END)
        self.moxa_result_text.insert(tk.END, friendly_report)
        self.moxa_result_text.config(state="disabled")
        
        # Informer l'utilisateur du résultat
        if analyzer.results['passed']:
            messagebox.showinfo("Analyse réussie", 
                              f"L'analyse est réussie avec un score de {analyzer.results['score']}/100.\n"
                              "Vous pouvez maintenant terminer cette étape.")
        else:
            messagebox.showwarning("Analyse échouée", 
                                 f"L'analyse a échoué avec un score de {analyzer.results['score']}/100.\n"
                                 "Veuillez ajuster les paramètres Moxa selon les recommandations et réessayer.")
                                 
        # Copier le fichier dans logs_moxa pour référence
        if not filepath.startswith(os.path.join(os.getcwd(), 'logs_moxa')):
            # Le fichier n'est pas déjà dans le dossier logs_moxa
            filename = os.path.basename(filepath)
            dest_path = os.path.join('logs_moxa', filename)
            try:
                with open(filepath, 'r', encoding='utf-8-sig', errors='ignore') as src:
                    content = src.read()
                with open(dest_path, 'w', encoding='utf-8') as dest:
                    dest.write(content)
                print(f"Fichier log copié vers {dest_path}")
            except Exception as e:
                print(f"Erreur lors de la copie du fichier log: {e}")

    def update_network_data(self):
        data = self.get_network_data()
        
        # Mise à jour des labels
        self.label_signal.config(text=f"Signal: {data['signal_percent']}%")
        self.label_rssi.config(text=f"RSSI: {data['rssi']} dBm")
        self.label_ping.config(text=f"Ping: {data['ping']} ms")
        
        self.label_ssid.config(text=f"SSID: {data['ssid']}")
        self.label_bssid.config(text=f"Point d'accès: {data['bssid']}")
        self.label_band.config(text=f"Bande: {data['band']}")
        self.label_channel.config(text=f"Canal: {data['channel']}")
        self.label_radio.config(text=f"Type de radio: {data['radio_type']}")
        self.label_speed.config(text=f"Débit: {data['rx_speed']} / {data['tx_speed']} Mbps")
        
        # Mise à jour du timestamp
        current_time = time.strftime("%H:%M:%S")
        self.timestamp_label.config(text=f"Dernière mise à jour: {current_time}")
        
        # Évaluation du signal
        if data['rssi'] > -65:  # Excellent
            self.configure(bg="#ccffcc")
            self.status = "Excellent"
            self.status_label.config(text="Signal excellent")
        elif data['rssi'] > -75:  # Bon
            self.configure(bg="#ffffcc")
            self.status = "Bon"
            self.status_label.config(text="Signal acceptable")
        else:  # Faible
            self.configure(bg="#ffcccc")
            self.status = "Faible"
            self.status_label.config(text="Signal faible - Zone à risque")
        
        # Si l'enregistrement est actif et le signal est faible, logger automatiquement
        if self.is_recording and data['rssi'] < -75:
            self.log_data("AUTO", "Signal faible détecté")
        
        # Si RSSI faible, jouer une notification
        if data['rssi'] < -75 and not self.is_recording:
            self.audit_manager.play_notification()
            if messagebox.askyesno("Point faible détecté", 
                                 "Un point faible a été détecté. Voulez-vous marquer cet emplacement ?"):
                self.mark_position()
        
        self.after(2000, self.update_network_data)

    def show_signal_quality(self):
        data = self.get_network_data()
        message = f"Analyse du signal WiFi:\n\n"
        
        if self.status == "Excellent":
            message += f"✅ Signal: Excellent ({data['signal_percent']}%, RSSI: {data['rssi']} dBm)\n"
        elif self.status == "Bon":
            message += f"⚠️ Signal: Acceptable ({data['signal_percent']}%, RSSI: {data['rssi']} dBm)\n"
        else:
            message += f"🛑 Signal: Faible ({data['signal_percent']}%, RSSI: {data['rssi']} dBm)\n"
        
        message += f"\nPoint d'accès: {data['bssid']}\n"
        message += f"Canal: {data['channel']} ({data['band']})\n"
        message += f"Type de radio: {data['radio_type']}\n"
        message += f"Débit: {data['rx_speed']} / {data['tx_speed']} Mbps\n"
        
        if data['ping'] > 100:
            message += f"🛑 Ping élevé: {data['ping']} ms > 100 ms\n"
        else:
            message += f"✅ Ping: {data['ping']} ms\n"
        
        message += "\nRecommandations:\n"
        if self.status == "Excellent":
            message += "• Emplacement optimal pour les AMR\n"
            message += "• Continuez sur cette trajectoire\n"
        elif self.status == "Bon":
            message += "• Emplacement acceptable, mais surveillez les fluctuations\n"
            message += "• Considérez un AP supplémentaire pour plus de fiabilité\n"
        else:
            message += "• Zone problématique pour les AMR - Risque de déconnexion\n"
            message += "• Vérifiez la distance avec l'AP et les obstacles\n"
            message += "• Installation d'un AP supplémentaire recommandée\n"
            message += "• Assurez une meilleure couverture avec chevauchement d'APs\n"
            
        messagebox.showinfo("Analyse du signal", message)

if __name__ == "__main__":
    try:
        app = AuditWifiApp()
        app.mainloop()
    except Exception as e:
        print(f"Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")

