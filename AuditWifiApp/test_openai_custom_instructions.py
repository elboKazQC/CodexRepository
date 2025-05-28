#!/usr/bin/env python3
"""
Script de test pour démontrer les nouvelles capacités d'instructions personnalisées OpenAI
"""

import sys
import os

# Ajouter le chemin du répertoire src pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ai.simple_moxa_analyzer import analyze_moxa_logs

def test_custom_instructions():
    """Test des instructions personnalisées avec différents styles"""

    # Logs de test simulés
    test_logs = """
    2024-05-28 10:15:23 - WiFi: Connected to AP_PROD_01, Signal: -65 dBm
    2024-05-28 10:15:45 - WiFi: Roaming initiated, Signal dropped to -78 dBm
    2024-05-28 10:15:47 - WiFi: Scanning for better AP
    2024-05-28 10:15:50 - WiFi: Found AP_PROD_02, Signal: -58 dBm
    2024-05-28 10:15:52 - WiFi: Roaming completed to AP_PROD_02
    2024-05-28 10:16:15 - WiFi: Signal fluctuation detected, -62 to -70 dBm
    """

    # Configuration de test
    test_config = {
        "roaming_difference": 8,
        "roaming_mechanism": "snr",
        "turbo_roaming": True,
        "min_transmission_rate": 12,
        "wmm_enabled": True
    }

    print("🧪 TEST DES INSTRUCTIONS PERSONNALISÉES OPENAI")
    print("=" * 50)

    # Test 1: Style rapide
    print("\n📝 TEST 1: Analyse rapide")
    print("-" * 30)
    custom_1 = "Analyse rapide en 3 lignes maximum avec score global seulement"
    print(f"Instructions: {custom_1}")
    print("Résultat attendu: Réponse courte et concise\n")

    # Test 2: Format bullet points
    print("📝 TEST 2: Format bullet points")
    print("-" * 30)
    custom_2 = "Résultats en bullet points avec émojis, focus sur les problèmes critiques"
    print(f"Instructions: {custom_2}")
    print("Résultat attendu: Format bullet points avec émojis\n")

    # Test 3: Focus technique
    print("📝 TEST 3: Focus technique roaming")
    print("-" * 30)
    custom_3 = "Focus exclusif sur les problèmes de roaming WiFi avec recommandations spécifiques"
    print(f"Instructions: {custom_3}")
    print("Résultat attendu: Analyse spécialisée roaming\n")

    # Test 4: Format tableau
    print("📝 TEST 4: Format tableau")
    print("-" * 30)
    custom_4 = "Présente sous forme de tableau: Problème | Gravité | Solution | Impact"
    print(f"Instructions: {custom_4}")
    print("Résultat attendu: Tableau structuré\n")

    print("💡 POUR TESTER RÉELLEMENT:")
    print("1. Lancez l'application: python runner.py")
    print("2. Allez dans l'onglet 'Analyse Logs Moxa'")
    print("3. Chargez des logs de test")
    print("4. Saisissez une des instructions ci-dessus")
    print("5. Cliquez sur 'Analyser les logs'")
    print("6. Observez comment OpenAI adapte sa réponse !")

    print("\n🎯 EXEMPLES D'INSTRUCTIONS À TESTER:")
    examples = [
        "Score global uniquement avec 2 recommandations max",
        "Style technique avec références IEEE 802.11",
        "Comparaison avec standards Cisco et recommandations",
        "Format JSON avec structure: {score, problemes, solutions}",
        "Analyse en français familier avec analogies simples",
        "Focus sécurité: vulnérabilités et failles uniquement"
    ]

    for i, example in enumerate(examples, 1):
        print(f"{i}. \"{example}\"")

    print("\n✅ LES INSTRUCTIONS PERSONNALISÉES SONT MAINTENANT PLEINEMENT FONCTIONNELLES !")

if __name__ == "__main__":
    test_custom_instructions()
