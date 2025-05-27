#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanceur d'application avec données de démonstration pré-chargées
pour tester les fonctionnalités de navigation temporelle et plein écran
"""

import sys
import os
import threading
import time
from datetime import datetime

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(__file__))

def launch_with_demo_data():
    """Lance l'application avec des données de démonstration"""
    try:
        # Importer les modules nécessaires
        import runner
        from demo_navigation import create_demo_samples

        print("🎯 LANCEMENT WIFI ANALYZER AVEC DÉMONSTRATION")
        print("=" * 60)

        # Créer les échantillons de démonstration
        print("📊 Préparation des données de démonstration...")
        demo_samples = create_demo_samples()
        print(f"✅ {len(demo_samples)} échantillons de démonstration créés")        # Créer et configurer l'application
        print("🚀 Initialisation de l'application...")
        import tkinter as tk
        root = tk.Tk()
        app = runner.NetworkAnalyzerUI(root)

        # Injecter les données de démonstration
        print("💉 Injection des données de démonstration...")
        app.samples.extend(demo_samples)

        # Configurer l'état initial pour la démonstration
        app.is_real_time = False  # Désactiver le temps réel pour la navigation

        # Mettre à jour l'affichage
        app.update_display()

        print("🎬 DÉMONSTRATION PRÊTE!")
        print("=" * 60)
        print("📋 FONCTIONNALITÉS À TESTER:")
        print("\n🎛️ NAVIGATION TEMPORELLE:")
        print("   • Mode navigation activé (temps réel désactivé)")
        print("   • Boutons ⏮️ ⏪ ⏸️ ⏩ ⏭️ disponibles")
        print("   • Slider de position pour navigation précise")
        print("   • Sélecteur de fenêtre d'affichage")

        print("\n🖥️ MODE PLEIN ÉCRAN:")
        print("   • Cliquez 'Plein Écran' pour présentation")
        print("   • Graphiques agrandis pour clients")
        print("   • Contrôles de navigation en plein écran")

        print("\n🎭 SCÉNARIOS DE DÉMONSTRATION:")
        print("   • 0-5 min: Connexion stable initiale")
        print("   • 5-8 min: Problèmes de signal (🔴)")
        print("   • 8-12 min: Récupération progressive")
        print("   • 12-20 min: Période stable")
        print("   • 20-25 min: Changement de point d'accès")
        print("   • 25-30 min: Connexion optimale finale")

        print("\n✨ POUR PRÉSENTATION PROFESSIONNELLE:")
        print("   • Naviguez vers les événements spécifiques")
        print("   • Montrez l'évolution dans le temps")
        print("   • Utilisez le plein écran pour impact visuel")
        print("   • Exportez avec la toolbar matplotlib")
          # Lancer l'interface graphique
        print("\n🎬 Lancement de l'interface graphique...")
        root.mainloop()

    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    print("🚀 Démarrage de la démonstration WiFi Analyzer...")
    launch_with_demo_data()
