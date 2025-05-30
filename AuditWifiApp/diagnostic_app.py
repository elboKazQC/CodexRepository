#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les problèmes de lancement de l'application
"""

import sys
import os
import traceback
import time

def test_imports():
    """Teste tous les imports nécessaires"""
    print("🔍 Test des imports...")

    try:
        import tkinter as tk
        print("✅ tkinter importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import tkinter: {e}")
        return False

    try:
        import matplotlib
        matplotlib.use('TkAgg')  # Backend pour tkinter
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
        print("✅ matplotlib importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import matplotlib: {e}")
        return False

    try:
        from runner import NetworkAnalyzerUI
        print("✅ NetworkAnalyzerUI importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import NetworkAnalyzerUI: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de l'import NetworkAnalyzerUI: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

    return True

def test_tkinter_window():
    """Teste la création d'une fenêtre tkinter simple"""
    print("\n🔍 Test d'une fenêtre tkinter simple...")

    try:
        import tkinter as tk
        root = tk.Tk()
        root.title("Test Window")
        root.geometry("300x200")

        label = tk.Label(root, text="Test réussi !")
        label.pack(pady=50)

        print("✅ Fenêtre tkinter créée")

        # Afficher la fenêtre pendant 2 secondes puis la fermer
        root.after(2000, root.destroy)
        root.mainloop()

        print("✅ Fenêtre tkinter fermée normalement")
        return True

    except Exception as e:
        print(f"❌ Erreur création fenêtre tkinter: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_app_creation():
    """Teste la création de l'application"""
    print("\n🔍 Test de création de l'application...")

    try:
        import tkinter as tk
        from runner import NetworkAnalyzerUI

        print("  → Création de la fenêtre root...")
        root = tk.Tk()
        root.withdraw()  # Masquer temporairement

        print("  → Création de NetworkAnalyzerUI...")
        app = NetworkAnalyzerUI(root)

        print("  → Application créée avec succès")

        # Test des attributs principaux
        if hasattr(app, 'master'):
            print("  ✅ Attribut master présent")
        if hasattr(app, 'samples'):
            print("  ✅ Attribut samples présent")
        if hasattr(app, 'analyzer'):
            print("  ✅ Attribut analyzer présent")

        root.destroy()
        print("✅ Application créée et détruite sans erreur")
        return True

    except Exception as e:
        print(f"❌ Erreur création application: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_full_launch():
    """Teste un lancement complet avec affichage"""
    print("\n🔍 Test de lancement complet...")

    try:
        import tkinter as tk
        from runner import NetworkAnalyzerUI

        print("  → Création de la fenêtre principale...")
        root = tk.Tk()
        root.title("Test WiFi Analyzer")

        print("  → Création de NetworkAnalyzerUI...")
        app = NetworkAnalyzerUI(root)

        print("  → Affichage de la fenêtre...")
        root.deiconify()  # Afficher la fenêtre
        root.update()

        print("✅ Application lancée avec succès")
        print("  → La fenêtre devrait être visible maintenant")
        print("  → Fermeture automatique dans 5 secondes...")

        # Fermer après 5 secondes
        root.after(5000, root.destroy)
        root.mainloop()

        print("✅ Application fermée normalement")
        return True

    except Exception as e:
        print(f"❌ Erreur lancement complet: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def check_environment():
    """Vérifie l'environnement système"""
    print("🔍 Vérification de l'environnement...")

    print(f"  • Python version: {sys.version}")
    print(f"  • Plateforme: {sys.platform}")
    print(f"  • Répertoire de travail: {os.getcwd()}")

    # Vérifier l'affichage
    if 'DISPLAY' in os.environ:
        print(f"  • DISPLAY: {os.environ['DISPLAY']}")
    else:
        print("  • DISPLAY: Non défini (normal sous Windows)")    # Vérifier les variables tkinter
    try:
        import tkinter as tk
        root = tk.Tk()
        print(f"  • Classe Tk: {root.__class__.__name__}")
        print(f"  • Gestionnaire: {root.tk.call('wm', 'manager', '.')}")
        root.destroy()
    except Exception as e:
        print(f"  • Erreur tkinter: {e}")
        pass

def main():
    """Fonction principale de diagnostic"""
    print("🚀 DIAGNOSTIC DE L'APPLICATION WIFI ANALYZER")
    print("=" * 50)

    # Vérifier l'environnement
    check_environment()
    print()

    # Tests séquentiels
    tests = [
        ("Imports", test_imports),
        ("Fenêtre tkinter simple", test_tkinter_window),
        ("Création application", test_app_creation),
        ("Lancement complet", test_full_launch)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test_name}: {e}")
            results.append((test_name, False))

        time.sleep(1)  # Pause entre les tests

    # Résumé
    print(f"\n{'='*50}")
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 50)

    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"  {test_name}: {status}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 Tous les tests sont passés !")
        print("💡 L'application devrait fonctionner. Essayez: python runner.py")
    else:
        print("\n⚠️ Certains tests ont échoué.")
        print("💡 Vérifiez les erreurs ci-dessus pour identifier le problème.")

if __name__ == "__main__":
    main()
