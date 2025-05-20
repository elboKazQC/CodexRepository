#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from moxa_unified_analyzer import MoxaUnifiedAnalyzer

def main():
    """Fonction principale pour lancer l'interface d'analyse unifiée Moxa"""
    root = tk.Tk()
    app = MoxaUnifiedAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")