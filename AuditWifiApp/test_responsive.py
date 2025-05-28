#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la navigation responsive pour écrans de portable
Simule une résolution de 1366x768 pour tester l'interface responsive
"""

import sys
import tkinter as tk
from runner import NetworkAnalyzerUI

class TestResponsiveUI:
    def __init__(self):
        self.root = tk.Tk()

        # Simuler un petit écran de portable
        self.root.geometry("1366x768")
        self.root.title("Test Responsive - Simulation Portable 1366x768")

        # Forcer la détection comme petit écran
        original_screenwidth = self.root.winfo_screenwidth
        original_screenheight = self.root.winfo_screenheight

        self.root.winfo_screenwidth = lambda: 1366
        self.root.winfo_screenheight = lambda: 768

        # Créer l'interface
        try:
            self.app = NetworkAnalyzerUI(self.root)
            print("✅ Interface responsive créée avec succès pour écran 1366x768")
            print("📱 Navigation adaptée pour petit écran activée")
            print("🎯 Boutons organisés en multiple lignes pour éviter le dépassement")
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'interface: {e}")
            sys.exit(1)

        # Restaurer les méthodes originales (optionnel)
        self.root.winfo_screenwidth = original_screenwidth
        self.root.winfo_screenheight = original_screenheight

    def run(self):
        print("\n🚀 Lancement du test responsive...")
        print("📋 Instructions de test:")
        print("  1. Vérifiez que tous les boutons de navigation sont visibles")
        print("  2. Le bouton 'Alerte précédente' doit être entièrement visible")
        print("  3. Les boutons doivent être organisés en plusieurs lignes")
        print("  4. Aucun élément ne doit dépasser du cadre de navigation")
        print("\n⏹️  Fermez la fenêtre pour terminer le test")

        self.root.mainloop()

if __name__ == "__main__":
    test_app = TestResponsiveUI()
    test_app.run()
