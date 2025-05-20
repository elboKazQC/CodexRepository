#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour lancer l'application MoxaAnalyzerUI
"""

import os
import sys
import traceback

print("Lancement de l'application...")
print(f"Version Python: {sys.version}")
print(f"Répertoire de travail: {os.getcwd()}")

try:
    # Importation des modules de base
    print("Importation des modules de base...")
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
    
    # Importation des modules spécifiques de l'application
    print("Importation des modules personnalisés...")
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
        filename="application.log",
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Charger les variables d'environnement
    load_dotenv()
    
    print("Initialisation de l'interface graphique...")
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
            # Votre code de configuration de l'UI ici...
            # Créer une interface simple pour tester
            test_frame = ttk.Frame(self.root, padding=20)
            test_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(test_frame, text="Application Analyseur Moxa démarrée avec succès!", font=("TkDefaultFont", 14)).pack(pady=20)
            ttk.Button(test_frame, text="Quitter", command=self.root.destroy).pack(pady=10)
    
    def main():
        """Fonction principale pour lancer l'application"""
        print("Initialisation de l'application...")
        root = tk.Tk()
        app = MoxaAnalyzerUI(root)
        print("Interface graphique créée. Démarrage de la boucle principale...")
        root.mainloop()
        print("Application terminée.")
    
    # Lancement de l'application
    print("Lancement de la fonction main...")
    main()
    
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"Erreur lors de l'exécution: {e}")
    traceback.print_exc()

input("Appuyez sur Entrée pour quitter...")
