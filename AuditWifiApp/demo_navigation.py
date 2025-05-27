#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Démonstration interactive des fonctionnalités de navigation temporelle
et du mode plein écran pour les présentations client
"""

import sys
import os
import time
import threading
from datetime import datetime, timedelta
from wifi.wifi_collector import WifiSample

# Ajouter le répertoire racine au path pour l'import
sys.path.insert(0, os.path.dirname(__file__))

def create_demo_samples():
    """Crée des échantillons de démonstration avec des événements réalistes"""
    samples = []
    base_time = datetime.now() - timedelta(minutes=30)

    # Simulation d'événements réseau réalistes sur 30 minutes
    for i in range(300):  # 300 échantillons = 1 toutes les 6 secondes
        current_time = base_time + timedelta(seconds=i * 6)

        # Simulation d'événements spécifiques
        if i < 50:  # Début - connexion stable
            signal = -45 + (i % 5)
            quality = 85 + (i % 10)
            status = "Connected"
        elif 50 <= i < 80:  # Problème de signal (minutes 5-8)
            signal = -75 + (i % 15)  # Signal faible et instable
            quality = 40 + (i % 20)
            status = "Poor Signal"
        elif 80 <= i < 120:  # Récupération progressive
            signal = -65 + min(20, (i-80))  # Amélioration graduelle
            quality = 50 + min(35, (i-80))
            status = "Recovering"
        elif 120 <= i < 200:  # Période stable
            signal = -50 + (i % 5)
            quality = 80 + (i % 15)
            status = "Connected"
        elif 200 <= i < 250:  # Changement de point d'accès
            signal = -60 + (i % 10)
            quality = 60 + (i % 25)
            status = "Roaming" if i % 3 == 0 else "Connected"
        else:  # Fin - connexion optimale
            signal = -40 + (i % 3)
            quality = 90 + (i % 8)
            status = "Excellent"

        # Choix du réseau selon la période
        if i < 100:
            ssid = "Corporate_WiFi_Main"
            bssid = "00:1A:2B:3C:4D:5E"
        elif i < 200:
            ssid = "Corporate_WiFi_Backup"
            bssid = "00:1A:2B:3C:4D:5F"
        else:
            ssid = "Corporate_WiFi_5G"
            bssid = "00:1A:2B:3C:4D:60"

        sample = WifiSample(
            timestamp=current_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
            ssid=ssid,
            bssid=bssid,
            signal_strength=signal,
            quality=max(0, min(100, quality)),
            channel=6 if "Main" in ssid else (11 if "Backup" in ssid else 36),
            band="2.4 GHz" if "5G" not in ssid else "5 GHz",
            status=status,
            transmit_rate=f'{max(10, 150 - abs(signal))} Mbps',
            receive_rate=f'{max(5, 75 - abs(signal)//2)} Mbps',
            raw_data={
                'TransmitRate': f'{max(10, 150 - abs(signal))} Mbps',
                'ReceiveRate': f'{max(5, 75 - abs(signal)//2)} Mbps',
                'Channel': 6 if "Main" in ssid else (11 if "Backup" in ssid else 36),
                'Band': "2.4 GHz" if "5G" not in ssid else "5 GHz",
                'EventType': 'Normal' if status == 'Connected' else 'Alert'
            }
        )
        samples.append(sample)

    return samples

def inject_samples_into_runner(samples):
    """Injecte les échantillons dans l'application runner"""
    try:
        import runner

        # Créer l'application si elle n'existe pas
        if not hasattr(runner, 'app') or runner.app is None:
            print("🚀 Initialisation de l'application...")
            runner.app = runner.WifiAnalysisApp()

        # Injecter les échantillons
        print(f"📊 Injection de {len(samples)} échantillons de démonstration...")
        for sample in samples:
            runner.app.wifi_samples.append(sample)

        # Mettre à jour l'affichage
        runner.app.update_display()
        print("✅ Échantillons injectés avec succès!")

        return runner.app

    except Exception as e:
        print(f"❌ Erreur lors de l'injection: {e}")
        return None

def start_demo():
    """Démarre la démonstration interactive"""
    print("🎯 DÉMONSTRATION NAVIGATION TEMPORELLE WIFI")
    print("=" * 60)

    # Créer les échantillons de démonstration
    print("📈 Création du scénario de démonstration...")
    samples = create_demo_samples()

    print(f"✅ {len(samples)} échantillons créés")
    print("📅 Période: 30 minutes d'historique")
    print("🎭 Scénarios inclus:")
    print("   • 🟢 Connexion stable (0-5 min)")
    print("   • 🔴 Problèmes de signal (5-8 min)")
    print("   • 🟡 Récupération progressive (8-12 min)")
    print("   • 🟢 Période stable (12-20 min)")
    print("   • 🔄 Changement de point d'accès (20-25 min)")
    print("   • 🟢 Connexion optimale (25-30 min)")

    print("\n🚀 Lancement de l'application avec données de démo...")

    # Injecter dans l'application
    app = inject_samples_into_runner(samples)

    if app:
        print("\n" + "=" * 60)
        print("🎛️ FONCTIONNALITÉS DE NAVIGATION DISPONIBLES:")
        print("=" * 60)
        print("\n1. 📊 NAVIGATION TEMPORELLE:")
        print("   • Décochez 'Temps réel' pour activer la navigation")
        print("   • Utilisez ⏮️ ⏪ ⏩ ⏭️ pour naviguer")
        print("   • Slider de position pour aller à un moment précis")
        print("   • Fenêtres d'affichage: 50, 100, 200, 500, 1000, Tout")

        print("\n2. 🖥️ MODE PLEIN ÉCRAN:")
        print("   • Bouton 'Plein Écran' pour présentation client")
        print("   • Graphiques agrandis avec contrôles")
        print("   • Parfait pour démonstrations professionnelles")

        print("\n3. 🎯 SCÉNARIOS À DÉMONTRER:")
        print("   • Minutes 5-8: Naviguez vers les problèmes de signal")
        print("   • Minutes 20-25: Montrez le changement de point d'accès")
        print("   • Comparez début vs fin pour montrer l'amélioration")

        print("\n✨ POUR PRÉSENTATION CLIENT:")
        print("   • Mode plein écran pour visibilité maximale")
        print("   • Navigation précise vers événements spécifiques")
        print("   • Exportation de captures avec toolbar matplotlib")
        print("   • Analyse professionnelle de la qualité réseau")

        print("\n🎬 Démonstration prête! L'application continue de fonctionner...")
        return True
    else:
        print("❌ Échec du lancement de la démonstration")
        return False

if __name__ == "__main__":
    # Test des échantillons
    print("🔧 Test de création des échantillons...")
    test_samples = create_demo_samples()
    print(f"✅ {len(test_samples)} échantillons de test créés")

    # Vérification de quelques échantillons
    print("\n📋 Aperçu des échantillons:")
    for i, sample in enumerate(test_samples[::50]):  # Échantillons tous les 50
        print(f"   {i*50:3d}: {sample.ssid} | {sample.signal_strength}dBm | {sample.quality}% | {sample.status}")

    print("\n🚀 Pour lancer la démonstration complète:")
    print("   1. Lancez: python runner.py")
    print("   2. Dans un autre terminal: python demo_navigation.py")
    print("   3. Ou importez ce module dans runner.py")
