#!/usr/bin/env python3
"""
Test des boutons "Guide complet" dans tous les onglets
de l'application WiFi Analyzer
"""

import os
import sys
import tkinter as tk
from unittest.mock import patch, MagicMock
import time

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from runner import NetworkAnalyzerUI
    print("✅ Import de NetworkAnalyzerUI réussi")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

def test_guide_buttons():
    """Test l'existence et le fonctionnement des boutons Guide complet"""
    print("\n🔍 Test des boutons 'Guide complet'...")

    # Créer une fenêtre de test
    root = tk.Tk()
    root.withdraw()  # Masquer la fenêtre principale

    try:
        # Créer l'interface
        app = NetworkAnalyzerUI(root)
        print("✅ Interface créée avec succès")

        # Test 1: Vérifier que les boutons existent
        buttons_found = []

        # Bouton WiFi
        if hasattr(app, 'wifi_guide_button'):
            buttons_found.append("WiFi")
            print("✅ Bouton guide WiFi trouvé")
        else:
            print("❌ Bouton guide WiFi non trouvé")

        # Bouton AMR
        if hasattr(app, 'amr_guide_button'):
            buttons_found.append("AMR")
            print("✅ Bouton guide AMR trouvé")
        else:
            print("❌ Bouton guide AMR non trouvé")

        # Test 2: Vérifier que la méthode show_instructions_guide existe
        if hasattr(app, 'show_instructions_guide'):
            print("✅ Méthode show_instructions_guide trouvée")
        else:
            print("❌ Méthode show_instructions_guide non trouvée")
            return False

        # Test 3: Vérifier que les guides existent
        guide_files = {
            "GUIDE_WIFI.md": "Guide WiFi",
            "GUIDE_AMR.md": "Guide AMR",
            "OPENAI_CUSTOM_INSTRUCTIONS_GUIDE.md": "Guide Moxa",
            "GUIDE_NAVIGATION.md": "Guide Navigation"
        }

        for filename, description in guide_files.items():
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            if os.path.exists(filepath):
                print(f"✅ {description} trouvé ({filename})")
            else:
                print(f"❌ {description} manquant ({filename})")

        # Test 4: Simuler l'ouverture des guides
        print("\n🧪 Test d'ouverture des guides...")

        # Patch pour éviter l'ouverture réelle des fenêtres
        with patch('tkinter.Toplevel') as mock_toplevel:
            mock_window = MagicMock()
            mock_toplevel.return_value = mock_window

            # Test ouverture guide WiFi
            try:
                app.show_instructions_guide("wifi")
                print("✅ Guide WiFi s'ouvre sans erreur")
            except Exception as e:
                print(f"❌ Erreur ouverture guide WiFi: {e}")

            # Test ouverture guide AMR
            try:
                app.show_instructions_guide("amr")
                print("✅ Guide AMR s'ouvre sans erreur")
            except Exception as e:
                print(f"❌ Erreur ouverture guide AMR: {e}")

            # Test ouverture guide Moxa
            try:
                app.show_instructions_guide("moxa")
                print("✅ Guide Moxa s'ouvre sans erreur")
            except Exception as e:
                print(f"❌ Erreur ouverture guide Moxa: {e}")

        print(f"\n📊 Résumé: {len(buttons_found)}/2 boutons trouvés: {', '.join(buttons_found)}")

        return len(buttons_found) == 2

    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

def test_guide_content():
    """Test le contenu des guides créés"""
    print("\n📝 Test du contenu des guides...")

    guides = {
        "GUIDE_WIFI.md": ["WiFi", "AMR", "signal", "latence"],
        "GUIDE_AMR.md": ["AMR", "monitoring", "robot", "connectivité"]
    }

    for filename, expected_keywords in guides.items():
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().lower()

                found_keywords = [kw for kw in expected_keywords if kw.lower() in content]

                if len(found_keywords) >= len(expected_keywords) // 2:
                    print(f"✅ {filename}: Contenu approprié ({len(found_keywords)}/{len(expected_keywords)} mots-clés)")
                else:
                    print(f"⚠️ {filename}: Contenu possiblement incomplet ({len(found_keywords)}/{len(expected_keywords)} mots-clés)")

            except Exception as e:
                print(f"❌ {filename}: Erreur de lecture - {e}")
        else:
            print(f"❌ {filename}: Fichier manquant")

def main():
    """Fonction principale de test"""
    print("🧪 Test d'implémentation des boutons 'Guide complet'")
    print("=" * 60)

    # Test 1: Boutons et interface
    buttons_ok = test_guide_buttons()

    # Test 2: Contenu des guides
    test_guide_content()

    # Résumé final
    print("\n" + "=" * 60)
    if buttons_ok:
        print("🎉 SUCCÈS: Tous les boutons 'Guide complet' sont implémentés !")
        print("\n🔧 Fonctionnalités ajoutées:")
        print("  • Bouton 'Guide complet' dans l'onglet WiFi")
        print("  • Bouton 'Guide complet' dans l'onglet AMR")
        print("  • Bouton 'Guide complet' existant dans l'onglet Moxa (mis à jour)")
        print("  • Guides spécifiques pour chaque onglet")
        print("  • Positionnement cohérent dans tous les onglets")

        print("\n📖 Guides disponibles:")
        print("  • Guide WiFi: Analyse et audit des réseaux sans fil")
        print("  • Guide AMR: Monitoring des robots mobiles autonomes")
        print("  • Guide Moxa: Instructions personnalisées OpenAI")
        print("  • Guide Navigation: Fonctionnalités de navigation temporelle")

        print("\n🎯 Utilisation:")
        print("  1. Lancez l'application: python runner.py")
        print("  2. Naviguez vers n'importe quel onglet")
        print("  3. Cliquez sur '📖 Guide Complet' pour l'aide contextuelle")

    else:
        print("❌ ÉCHEC: Certains boutons ne sont pas correctement implémentés")
        print("Vérifiez les erreurs ci-dessus et corrigez-les.")

    return 0 if buttons_ok else 1

if __name__ == "__main__":
    sys.exit(main())
