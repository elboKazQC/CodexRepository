# -*- coding: utf-8 -*-
import os
import tkinter as tk
from moxa_config_analyzer import MoxaConfigAnalyzer

def main():
    """Fonction principale pour lancer l'outil d'optimisation Moxa"""
    # Créer les dossiers nécessaires s'ils n'existent pas
    os.makedirs("logs_moxa", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    # Lancer l'interface graphique
    root = tk.Tk()
    app = MoxaConfigAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()