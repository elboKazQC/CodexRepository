#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de débogage pour identifier les problèmes de démarrage
"""

import sys
import traceback

def test_imports():
    """Teste tous les imports un par un"""
    print("=== Test des imports ===")

    try:
        print("✓ sys importé")
        import json
        print("✓ json importé")
        import logging
        print("✓ logging importé")
        from datetime import datetime
        print("✓ datetime importé")
        import tkinter as tk
        print("✓ tkinter importé")
        from tkinter import ttk, messagebox, filedialog, simpledialog
        print("✓ tkinter.ttk importé")

        import matplotlib
        print("✓ matplotlib importé")
        matplotlib.use('TkAgg')
        print("✓ matplotlib backend configuré")

        import matplotlib.pyplot as plt
        print("✓ matplotlib.pyplot importé")
        plt.ioff()
        print("✓ matplotlib en mode non-interactif")

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        print("✓ FigureCanvasTkAgg importé")
        from matplotlib.backends._backend_tk import NavigationToolbar2Tk
        print("✓ NavigationToolbar2Tk importé")
        from matplotlib.figure import Figure
        print("✓ Figure importé")
        from matplotlib.widgets import SpanSelector
        print("✓ SpanSelector importé")
        import matplotlib.dates as mdates
        print("✓ mdates importé")
        import numpy as np
        print("✓ numpy importé")

        from typing import List, Optional, Dict
        print("✓ typing importé")
        import os
        print("✓ os importé")
        import subprocess
        print("✓ subprocess importé")
        import re
        print("✓ re importé")

        from dotenv import load_dotenv
        print("✓ dotenv importé")
        load_dotenv()
        print("✓ variables d'environnement chargées")

        # Maintenant tester les imports locaux
        try:
            from network_analyzer import NetworkAnalyzer
            print("✓ NetworkAnalyzer importé")
        except ImportError as e:
            print(f"❌ Erreur import NetworkAnalyzer: {e}")

        try:
            from amr_monitor import AMRMonitor
            print("✓ AMRMonitor importé")
        except ImportError as e:
            print(f"❌ Erreur import AMRMonitor: {e}")

        try:
            from wifi.wifi_collector import WifiSample
            print("✓ WifiSample importé")
        except ImportError as e:
            print(f"❌ Erreur import WifiSample: {e}")

        try:
            from src.ai.simple_moxa_analyzer import analyze_moxa_logs
            print("✓ analyze_moxa_logs importé")
        except ImportError as e:
            print(f"❌ Erreur import analyze_moxa_logs: {e}")

        try:
            from config_manager import ConfigurationManager
            print("✓ ConfigurationManager importé")
        except ImportError as e:
            print(f"❌ Erreur import ConfigurationManager: {e}")

        try:
            from mac_tag_manager import MacTagManager
            print("✓ MacTagManager importé")
        except ImportError as e:
            print(f"❌ Erreur import MacTagManager: {e}")

        print("\n=== Tous les imports de base réussis ! ===")
        return True

    except Exception as e:
        print(f"❌ Erreur lors des imports: {e}")
        traceback.print_exc()
        return False

def test_main_class():
    """Teste l'instanciation de la classe principale"""
    print("\n=== Test de la classe principale ===")

    try:
        import tkinter as tk
        from runner import NetworkAnalyzerUI

        print("✓ Création de la fenêtre Tk...")
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre pour les tests

        print("✓ Instanciation de NetworkAnalyzerUI...")
        app = NetworkAnalyzerUI(root)

        print("✓ Classe principale créée avec succès!")
        root.destroy()
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'instanciation: {e}")
        traceback.print_exc()
        return False

def main():
    """Fonction principale de débogage"""
    print("🔍 Diagnostic de démarrage de l'application WiFi Analyzer")
    print("=" * 60)

    # Test des imports
    imports_ok = test_imports()

    if imports_ok:
        # Test de la classe principale
        main_class_ok = test_main_class()

        if main_class_ok:
            print("\n✅ Tous les tests réussis ! L'application devrait démarrer.")

            # Essayer de démarrer normalement
            print("\n🚀 Tentative de démarrage normal...")
            try:
                import tkinter as tk
                from runner import NetworkAnalyzerUI

                root = tk.Tk()
                app = NetworkAnalyzerUI(root)
                print("✅ Application démarrée avec succès!")

                # Demander si on veut continuer avec l'interface
                response = input("\nVoulez-vous ouvrir l'interface graphique ? (o/n): ")
                if response.lower() in ['o', 'oui', 'y', 'yes']:
                    root.mainloop()
                else:
                    root.destroy()

            except Exception as e:
                print(f"❌ Erreur lors du démarrage normal: {e}")
                traceback.print_exc()
        else:
            print("\n❌ Problème avec la classe principale")
    else:
        print("\n❌ Problème avec les imports")

    print("\n🔍 Diagnostic terminé.")

if __name__ == "__main__":
    main()
