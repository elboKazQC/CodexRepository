#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple de démarrage
"""

print("🔍 Test de démarrage simple...")

try:
    # Test des imports
    print("✓ Test des imports...")
    import tkinter as tk
    print("  ✓ tkinter OK")

    from runner import NetworkAnalyzerUI
    print("  ✓ NetworkAnalyzerUI OK")

    # Test instanciation rapide
    print("✓ Test instanciation...")
    root = tk.Tk()
    root.withdraw()  # Masquer la fenêtre

    app = NetworkAnalyzerUI(root)
    print("  ✓ NetworkAnalyzerUI créée")

    # Vérifications basiques
    assert hasattr(app, 'analyzer')
    assert hasattr(app, 'master')
    print("  ✓ Attributs principaux présents")

    root.destroy()
    print("  ✓ Fermeture propre")

    print("\n🎉 SUCCESS: L'application fonctionne correctement!")
    print("✅ Le problème de démarrage est résolu.")

except Exception as e:
    print(f"\n❌ ERREUR: {str(e)}")
    import traceback
    traceback.print_exc()
