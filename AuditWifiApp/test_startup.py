#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier que l'application WiFi Analyzer démarre correctement
"""

import sys
import time
import threading
import tkinter as tk
from runner import NetworkAnalyzerUI, main

def test_quick_startup():
    """Test rapide de démarrage de l'application"""
    print("🧪 Test de démarrage rapide de l'application...")
    
    try:
        # Créer une fenêtre de test
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre
        
        print("✓ Tkinter OK")
        
        # Tester l'instanciation de la classe principale
        app = NetworkAnalyzerUI(root)
        print("✓ NetworkAnalyzerUI instanciée avec succès")
        
        # Vérifier que les composants principaux existent
        assert hasattr(app, 'analyzer'), "Analyzer manquant"
        assert hasattr(app, 'master'), "Master window manquante"
        assert hasattr(app, 'notebook'), "Notebook manquant"
        print("✓ Composants principaux présents")
        
        # Fermer proprement
        root.destroy()
        print("✓ Fermeture propre")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        return False

def test_with_gui():
    """Test avec interface graphique visible"""
    print("🖥️ Test avec interface graphique...")
    
    def close_after_delay():
        """Ferme l'application après 5 secondes"""
        time.sleep(5)
        print("⏰ Fermeture automatique après 5 secondes")
        root.quit()
    
    try:
        root = tk.Tk()
        app = NetworkAnalyzerUI(root)
        
        # Démarrer un timer pour fermer automatiquement
        timer_thread = threading.Thread(target=close_after_delay, daemon=True)
        timer_thread.start()
        
        print("✓ Interface affichée - fermeture automatique dans 5 secondes")
        print("  (Vous pouvez fermer manuellement si l'interface s'affiche)")
        
        root.mainloop()
        print("✓ Test GUI terminé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test GUI: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 TESTS DE DÉMARRAGE - WiFi Analyzer")
    print("=" * 60)
    
    # Test 1: Démarrage rapide sans GUI
    print("\n1️⃣ Test de démarrage rapide...")
    quick_test_ok = test_quick_startup()
    
    if quick_test_ok:
        print("\n✅ Test rapide RÉUSSI")
        
        # Test 2: Interface graphique
        print("\n2️⃣ Test interface graphique...")
        gui_test_ok = test_with_gui()
        
        if gui_test_ok:
            print("\n🎉 TOUS LES TESTS RÉUSSIS!")
            print("✅ L'application WiFi Analyzer fonctionne correctement")
            print("\n📝 Résumé:")
            print("   • L'application se lance sans erreur")
            print("   • L'interface graphique s'affiche")
            print("   • Tous les composants sont présents")
            print("   • La fermeture se fait proprement")
        else:
            print("\n⚠️ Problème avec l'interface graphique")
    else:
        print("\n❌ ÉCHEC du test de base")
        
    print("\n" + "=" * 60)
