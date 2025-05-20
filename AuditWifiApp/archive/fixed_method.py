# -*- coding: utf-8 -*-
# Méthode corrigée pour remplacer dans main.py

def show_signal_quality(self):
    data = self.get_network_data()
    message = f"Analyse du signal WiFi:\n\n"
    
    if self.status == "Excellent":
        message += f"✅ Signal: Excellent ({data['signal_percent']}%, RSSI: {data['rssi']} dBm)\n"
    elif self.status == "Bon":
        message += f"⚠️ Signal: Acceptable ({data['signal_percent']}%, RSSI: {data['rssi']} dBm)\n"
    else:
        message += f"🛑 Signal: Faible ({data['signal_percent']}%, RSSI: {data['rssi']} dBm)\n"
    
    message += f"\nPoint d'accès: {data['bssid']}\n"
    message += f"Canal: {data['channel']} ({data['band']})\n"
    message += f"Type de radio: {data['radio_type']}\n"
    message += f"Débit: {data['rx_speed']} / {data['tx_speed']} Mbps\n"
    
    if data['ping'] > 100:
        message += f"🛑 Ping élevé: {data['ping']} ms > 100 ms\n"
    else:
        message += f"✅ Ping: {data['ping']} ms\n"
    
    message += "\nRecommandations:\n"
    if self.status == "Excellent":
        message += "• Emplacement optimal pour les AMR\n"
        message += "• Continuez sur cette trajectoire\n"
    elif self.status == "Bon":
        message += "• Emplacement acceptable, mais surveillez les fluctuations\n"
        message += "• Considérez un AP supplémentaire pour plus de fiabilité\n"
    else:
        message += "• Zone problématique pour les AMR - Risque de déconnexion\n"
        message += "• Vérifiez la distance avec l'AP et les obstacles\n"
        message += "• Installation d'un AP supplémentaire recommandée\n"
        message += "• Assurez une meilleure couverture avec chevauchement d'APs\n"
        
    messagebox.showinfo("Analyse du signal", message)