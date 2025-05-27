#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le rapport final WiFi
"""

import tkinter as tk
from runner import NetworkAnalyzerUI
from wifi.wifi_collector import WifiSample
from datetime import datetime
import time

def test_rapport_final():
    """Test de la génération du rapport final"""

    # Créer l'interface
    root = tk.Tk()
    app = NetworkAnalyzerUI(root)

    # Simuler quelques échantillons de données
    sample_data = [
        {"signal": -45, "quality": 85},
        {"signal": -48, "quality": 82},
        {"signal": -52, "quality": 78},
        {"signal": -47, "quality": 83},
        {"signal": -50, "quality": 80},
        {"signal": -55, "quality": 75},
        {"signal": -49, "quality": 81},
        {"signal": -46, "quality": 84},
        {"signal": -51, "quality": 79},
        {"signal": -53, "quality": 77},
    ]

    # Créer des échantillons WiFi simulés
    for i, data in enumerate(sample_data):
        sample = WifiSample(
            timestamp=datetime.now(),
            signal_strength=data["signal"],
            quality=data["quality"],
            ssid="TestNetwork",
            bssid="00:11:22:33:44:55",
            raw_data={
                "TransmitRate": "54 Mbps",
                "ReceiveRate": "48 Mbps"
            }
        )
        app.samples.append(sample)

        # Ajouter aussi à l'historique pour les alertes
        alerts = []
        if data["signal"] < -50:
            alerts.append("Signal faible")
        if data["quality"] < 80:
            alerts.append("Qualité moyenne")

        app.wifi_history_entries.append({
            'timestamp': f"12:0{i}:00",
            'signal': data["signal"],
            'quality': data["quality"],
            'alerts': alerts
        })

    # Générer le rapport final
    print("Génération du rapport final...")
    app.generate_final_network_report()

    print("Rapport généré avec succès!")
    print("Vérifiez l'onglet 'Rapport Final' dans l'interface.")

    # Lancer l'interface pour voir le résultat
    root.mainloop()

if __name__ == "__main__":
    test_rapport_final()
