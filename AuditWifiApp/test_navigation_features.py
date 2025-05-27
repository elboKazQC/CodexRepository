#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test des nouvelles fonctionnalités de navigation temporelle et plein écran
"""

import tkinter as tk
from wifi.wifi_collector import WifiSample
from datetime import datetime
import time

def test_navigation_features():
    """Test des fonctionnalités de navigation et plein écran"""

    # Créer quelques échantillons de test
    test_samples = []
    for i in range(50):
        sample = WifiSample(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            ssid=f"TestWiFi_{i}",
            bssid=f"00:11:22:33:44:{i:02x}",
            signal_strength=-60 + (i % 30) - 15,  # Variation de -75 à -45 dBm
            quality=70 + (i % 25),  # Variation de 70% à 95%
            channel=6 + (i % 11),  # Canaux 6-16
            band="2.4 GHz" if i % 2 == 0 else "5 GHz",
            status="Connected" if i % 3 == 0 else "Available",
            transmit_rate=f'{50 + i} Mbps',
            receive_rate=f'{25 + i} Mbps',
            raw_data={
                'TransmitRate': f'{50 + i} Mbps',
                'ReceiveRate': f'{25 + i} Mbps',
                'Channel': 6 + (i % 11),
                'Band': "2.4 GHz" if i % 2 == 0 else "5 GHz"
            }
        )
        test_samples.append(sample)

    print("✅ Échantillons de test créés avec succès")
    print(f"📊 {len(test_samples)} échantillons générés")
    print("📶 Signal variant de -75 à -45 dBm")
    print("🎯 Qualité variant de 70% à 95%")
    print("\nCes échantillons peuvent être utilisés pour tester:")
    print("• 🎛️ Navigation temporelle (boutons précédent/suivant)")
    print("• 📊 Slider de position")
    print("• 🖥️ Mode plein écran")
    print("• ⏱️ Basculement temps réel/navigation")
    print("• 🔍 Fenêtres d'affichage (50, 100, 200, 500, 1000, Tout)")

    # Instructions pour l'utilisateur
    print("\n" + "="*60)
    print("INSTRUCTIONS POUR TESTER LES NOUVELLES FONCTIONNALITÉS:")
    print("="*60)
    print("\n1. 🚀 Lancez l'application: python runner.py")
    print("\n2. 📡 Démarrez la collecte WiFi")
    print("\n3. 🎛️ NAVIGATION TEMPORELLE:")
    print("   • Décochez 'Temps réel' pour activer la navigation")
    print("   • Utilisez les boutons ⏮️ ⏪ ⏸️ ⏩ ⏭️")
    print("   • Déplacez le slider de position")
    print("   • Changez la taille de fenêtre d'affichage")

    print("\n4. 🖥️ MODE PLEIN ÉCRAN:")
    print("   • Cliquez sur 'Plein Écran' pour ouvrir une fenêtre dédiée")
    print("   • Graphiques plus grands pour présentation client")
    print("   • Contrôles de navigation disponibles en plein écran")
    print("   • Parfait pour montrer des événements spécifiques")

    print("\n5. 📊 ANALYSE TEMPORELLE:")
    print("   • Naviguez vers des moments spécifiques")
    print("   • Identifiez les pics de problèmes")
    print("   • Montrez l'évolution dans le temps")
    print("   • Exportez des captures d'écran avec la toolbar matplotlib")

    print("\n✨ CES FONCTIONNALITÉS PERMETTENT:")
    print("• Analyse professionnelle pour clients")
    print("• Navigation précise dans l'historique")
    print("• Présentation claire des problèmes détectés")
    print("• Démonstration des améliorations réseau")

    return test_samples

if __name__ == "__main__":
    print("🎯 Test des nouvelles fonctionnalités de navigation WiFi")
    print("=" * 60)
    test_navigation_features()
