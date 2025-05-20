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
    # Importation du module runner_fixed_new
    print("Tentative d'importation du module runner_fixed_new...")
    import runner_fixed_new
    
    # Lancement de l'application
    print("Lancement de la fonction main...")
    runner_fixed_new.main()
    
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"Erreur lors de l'exécution: {e}")
    traceback.print_exc()

input("Appuyez sur Entrée pour quitter...")
