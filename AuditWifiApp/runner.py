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
from unittest.mock import MagicMock
import yaml

from heatmap_generator import generate_heatmap
from network_analyzer import NetworkAnalyzer
from network_scanner import scan_wifi
from wifi.wifi_collector import WifiSample
from src.ai.simple_moxa_analyzer import analyze_moxa_logs
from config_manager import ConfigurationManager
from ui.wifi_view import WifiView
from ui.moxa_view import MoxaView
from ui.amr_view import AmrMonitorView

class NetworkAnalyzerUI:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("Analyseur Réseau WiFi & Moxa")
        self.master.state('zoomed')

        # Initialisation des composants
        self.analyzer = NetworkAnalyzer()

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

        # Création de l'interface
        self.create_interface()

    def setup_graphs(self) -> None:

        """Deprecated compatibility method for tests."""
        # The graph setup logic now lives in WifiView.
        pass


    def create_interface(self):
        """Crée l'interface principale"""
        # Setup ttk style for consistent look
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TNotebook.Tab', padding=[10, 4])

        # Notebook pour les différentes vues
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # === Onglet WiFi ===
        # Créer un frame pour contenir la vue WiFi
        wifi_frame = ttk.Frame(self.notebook)
        wifi_frame.columnconfigure(0, weight=1)
        wifi_frame.rowconfigure(0, weight=1)
        self.wifi_view = WifiView(wifi_frame, self.analyzer)
        self.wifi_view.frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.notebook.add(wifi_frame, text="Analyse WiFi")

        # === Onglet Moxa ===
        # Créer un frame pour contenir la vue Moxa
        moxa_frame = ttk.Frame(self.notebook)
        moxa_frame.columnconfigure(0, weight=1)
        moxa_frame.rowconfigure(0, weight=1)
        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        self.moxa_view = MoxaView(moxa_frame, self.config_dir, self.default_config)
        self.moxa_view.frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.notebook.add(moxa_frame, text="Analyse Moxa")

        # === Onglet Monitoring AMR ===
        amr_frame = ttk.Frame(self.notebook)
        amr_frame.columnconfigure(0, weight=1)
        amr_frame.rowconfigure(0, weight=1)
        self.amr_view = AmrMonitorView(amr_frame)
        self.amr_view.frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.notebook.add(amr_frame, text="Monitoring AMR")


def main():
    """Point d'entrée de l'application"""
    try:
        root = tk.Tk()
        from bootstrap_ui import BootstrapNetworkAnalyzerUI
        app = BootstrapNetworkAnalyzerUI(root, theme="darkly")
        root.mainloop()
    except Exception as e:
        print(f"Erreur fatale: {str(e)}")
        messagebox.showerror("Erreur fatale", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
