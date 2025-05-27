#!/usr/bin/env python3
"""
Test des nouveaux seuils avec les vraies valeurs d'alerte de l'utilisateur
"""

def test_old_vs_new_thresholds():
    """Compare l'ancien et le nouveau système d'alertes"""

    # Valeurs réelles de l'utilisateur
    signal = -59  # dBm
    quality = 82  # %
    tx_rate = 360  # Mbps
    rx_rate = 6    # Mbps

    print("🔍 ANALYSE DES ALERTES - AVANT vs APRÈS")
    print("=" * 60)
    print(f"📊 Valeurs réelles :")
    print(f"   Signal: {signal} dBm")
    print(f"   Qualité: {quality}%")
    print(f"   TX: {tx_rate} Mbps")
    print(f"   RX: {rx_rate} Mbps")
    print()

    # ===== ANCIEN SYSTÈME =====
    print("🔴 ANCIEN SYSTÈME (trop strict) :")
    old_alerts = []

    # Signal (anciens seuils trop stricts)
    if signal < -80:
        old_alerts.append(f"🔴 Signal CRITIQUE : {signal} dBm")
    elif signal < -75:
        old_alerts.append(f"⚠️ Signal faible : {signal} dBm")

    # Qualité (anciens seuils trop stricts)
    if quality < 30:
        old_alerts.append(f"🔴 Qualité CRITIQUE : {quality}%")
    elif quality < 50:
        old_alerts.append(f"⚠️ Qualité faible : {quality}%")

    # Débits (ancien seuil trop strict)
    if min(tx_rate, rx_rate) < 24:
        old_alerts.append(f"⚠️ Débit insuffisant : TX: {tx_rate} Mbps, RX: {rx_rate} Mbps")

    if old_alerts:
        for alert in old_alerts:
            print(f"   {alert}")
    else:
        print("   ✅ Aucune alerte")

    print()

    # ===== NOUVEAU SYSTÈME =====
    print("✅ NOUVEAU SYSTÈME (réaliste) :")
    new_alerts = []

    # Signal (nouveaux seuils réalistes)
    if signal < -85:
        new_alerts.append(f"🔴 Signal CRITIQUE : {signal} dBm")
    elif signal < -80:
        new_alerts.append(f"⚠️ Signal faible : {signal} dBm")

    # Qualité (nouveaux seuils réalistes)
    if quality < 20:
        new_alerts.append(f"🔴 Qualité CRITIQUE : {quality}%")
    elif quality < 40:
        new_alerts.append(f"⚠️ Qualité faible : {quality}%")

    # Débits (nouvelle logique intelligente)
    min_tx_critical = 10
    min_rx_critical = 2
    min_tx_warning = 50
    min_rx_warning = 5

    if tx_rate < min_tx_critical and rx_rate < min_rx_critical:
        new_alerts.append(f"🔴 Débits CRITIQUES : TX: {tx_rate} Mbps, RX: {rx_rate} Mbps")
    elif tx_rate < min_tx_warning and rx_rate < min_rx_warning:
        new_alerts.append(f"⚠️ Débits faibles : TX: {tx_rate} Mbps, RX: {rx_rate} Mbps")

    if new_alerts:
        for alert in new_alerts:
            print(f"   {alert}")
    else:
        print("   ✅ Aucune alerte - Réseau en excellent état !")

    print()
    print("=" * 60)
    print("📈 RÉSULTAT :")
    print(f"   Ancien système : {len(old_alerts)} alerte(s)")
    print(f"   Nouveau système : {len(new_alerts)} alerte(s)")
    print()

    if len(new_alerts) < len(old_alerts):
        print("🎯 SUCCÈS ! Le nouveau système élimine les fausses alertes")
        print("   Votre réseau est effectivement en excellent état !")
    else:
        print("⚠️ Les alertes persistent - investigation nécessaire")

if __name__ == "__main__":
    test_old_vs_new_thresholds()
