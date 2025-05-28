#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import math

def test_screen_detection():
    """Teste la détection d'écran portable basée sur le DPI et la taille physique"""

    # Créer une fenêtre temporaire pour les mesures
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre

    try:
        # Obtenir les informations d'écran
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        print(f"=== DÉTECTION D'ÉCRAN PORTABLE ===")
        print(f"Résolution détectée: {screen_width}x{screen_height}")

        try:
            # Calculer le DPI et la taille physique
            dpi = root.winfo_fpixels('1i')
            diagonal_pixels = math.sqrt(screen_width**2 + screen_height**2)
            diagonal_inches = diagonal_pixels / dpi

            print(f"DPI détecté: {dpi:.1f}")
            print(f"Diagonale physique: {diagonal_inches:.1f} pouces")

            # Critères de détection d'écran portable
            is_portable_size = diagonal_inches <= 16.5  # Écrans <= 16.5" sont généralement portables
            is_low_res = screen_width < 1366 or screen_height < 768  # Résolutions classiquement faibles
            is_high_dpi = dpi > 110  # DPI élevé, souvent signe d'écran portable haute densité

            print(f"\n=== ANALYSE DES CRITÈRES ===")
            print(f"Écran physique ≤ 16.5″: {'✅' if is_portable_size else '❌'} ({diagonal_inches:.1f}″)")
            print(f"Résolution faible: {'✅' if is_low_res else '❌'} ({screen_width}x{screen_height})")
            print(f"DPI élevé (>110): {'✅' if is_high_dpi else '❌'} ({dpi:.1f})")

            # Décision finale
            is_portable = is_portable_size or is_low_res or is_high_dpi

            print(f"\n=== RÉSULTAT ===")
            if is_portable:
                print("📱 ÉCRAN PORTABLE DÉTECTÉ")
                if is_portable_size:
                    print(f"   → Raison: Taille physique ({diagonal_inches:.1f}″ ≤ 16.5″)")
                elif is_high_dpi:
                    print(f"   → Raison: DPI élevé ({dpi:.1f} > 110)")
                elif is_low_res:
                    print(f"   → Raison: Résolution faible ({screen_width}x{screen_height})")

                print("   → Interface responsive sera activée")
                print("   → Mise en page adaptée aux petits écrans")
                print("   → Boutons de navigation compacts")
            else:
                print("🖥️ GRAND ÉCRAN DÉTECTÉ")
                print("   → Interface standard sera utilisée")
                print("   → Mise en page normale")
                print("   → Fenêtre maximisée")

            # Estimation du type d'écran
            print(f"\n=== ESTIMATION DU TYPE D'ÉCRAN ===")
            if diagonal_inches <= 13:
                print(f"📱 Probablement un laptop ultraportable (≤13″)")
            elif diagonal_inches <= 16:
                print(f"💻 Probablement un laptop standard (13-16″)")
            elif diagonal_inches <= 20:
                print(f"🖥️ Probablement un écran de bureau compact (17-20″)")
            elif diagonal_inches <= 27:
                print(f"🖥️ Probablement un écran de bureau standard (21-27″)")
            else:
                print(f"🖥️ Probablement un grand écran de bureau (>27″)")

            # Recommandations spécifiques pour différents cas
            print(f"\n=== RECOMMANDATIONS ===")
            if screen_width == 1920 and screen_height == 1080:
                if diagonal_inches <= 16:
                    print("⚠️  Résolution Full HD sur petit écran détectée")
                    print("   → Éléments d'interface peuvent sembler trop petits")
                    print("   → Mode responsive fortement recommandé")
                else:
                    print("✅ Résolution Full HD sur grand écran")
                    print("   → Interface standard appropriée")

            return is_portable, diagonal_inches, dpi

        except Exception as e:
            print(f"❌ Erreur lors du calcul DPI: {str(e)}")
            print("   → Utilisation de la détection par résolution uniquement")

            is_portable = screen_width < 1366 or screen_height < 768
            print(f"\n=== RÉSULTAT (MODE FALLBACK) ===")
            if is_portable:
                print("📱 ÉCRAN PORTABLE DÉTECTÉ (par résolution)")
            else:
                print("🖥️ GRAND ÉCRAN DÉTECTÉ (par résolution)")

            return is_portable, None, None

    finally:
        root.destroy()

if __name__ == "__main__":
    print("🔍 Test de détection d'écran portable pour l'application WiFi Analyzer")
    print("=" * 60)

    try:
        is_portable, diagonal, dpi = test_screen_detection()

        print(f"\n" + "=" * 60)
        print("✅ Test terminé avec succès!")

        # Instructions pour l'utilisateur
        print(f"\n=== INSTRUCTIONS ===")
        if is_portable:
            print("👉 Votre écran a été détecté comme portable.")
            print("   L'application utilisera automatiquement:")
            print("   • Interface compacte et responsive")
            print("   • Boutons de navigation simplifiés")
            print("   • Fenêtre optimisée (95% de l'écran)")
            print("   • Polices et espacements adaptés")
        else:
            print("👉 Votre écran a été détecté comme un grand écran.")
            print("   L'application utilisera:")
            print("   • Interface standard")
            print("   • Tous les contrôles de navigation")
            print("   • Fenêtre maximisée")
            print("   • Polices et espacements normaux")

    except Exception as e:
        print(f"❌ Erreur durant le test: {str(e)}")
        print("   Veuillez vérifier votre environnement Tkinter")
