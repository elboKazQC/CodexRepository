#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rapide de détection d'écran portable
Compatible avec votre environnement Windows
"""

def main():
    print("🔍 Test de détection d'écran portable")
    print("=" * 50)

    try:
        import tkinter as tk
        import math

        # Créer une fenêtre temporaire
        root = tk.Tk()
        root.withdraw()  # Masquer

        # Informations de base
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()

        print(f"Résolution: {width}x{height}")

        try:
            # Calcul DPI et taille physique
            dpi = root.winfo_fpixels('1i')
            diagonal_px = math.sqrt(width**2 + height**2)
            diagonal_in = diagonal_px / dpi

            print(f"DPI: {dpi:.1f}")
            print(f"Diagonale: {diagonal_in:.1f} pouces")

            # Critères de détection
            small_size = diagonal_in <= 16.5
            low_res = width < 1366 or height < 768
            high_dpi = dpi > 110

            is_portable = small_size or low_res or high_dpi

            print(f"\nCritères:")
            print(f"  Petit écran (≤16.5″): {'✅' if small_size else '❌'}")
            print(f"  Résolution faible: {'✅' if low_res else '❌'}")
            print(f"  DPI élevé (>110): {'✅' if high_dpi else '❌'}")

            print(f"\nRésultat:")
            if is_portable:
                print("📱 ÉCRAN PORTABLE → Interface responsive")
                print("   • Boutons compacts")
                print("   • Navigation simplifiée")
                print("   • Fenêtre 95% écran")
            else:
                print("🖥️ GRAND ÉCRAN → Interface standard")
                print("   • Interface complète")
                print("   • Fenêtre maximisée")

        except Exception as e:
            print(f"Erreur DPI: {e}")
            is_portable = width < 1366 or height < 768
            print(f"Mode fallback: {'Portable' if is_portable else 'Grand écran'}")

        root.destroy()

    except Exception as e:
        print(f"Erreur: {e}")

    print("\n✅ Test terminé")
    input("Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main()
