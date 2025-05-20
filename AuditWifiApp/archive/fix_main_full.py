# -*- coding: utf-8 -*-
# Script pour réparer automatiquement le fichier main.py

def fix_main_py():
    try:
        # Lire le contenu du fichier
        with open('main.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Chercher la méthode show_signal_quality
        method_start = -1
        method_end = -1
        
        for i, line in enumerate(lines):
            if 'def show_signal_quality(self):' in line:
                method_start = i
                break
        
        if method_start == -1:
            print("Méthode show_signal_quality non trouvée!")
            return False
        
        # Trouver la fin de la méthode
        for i in range(method_start + 1, len(lines)):
            if lines[i].startswith('    def ') or lines[i].startswith('if __name__'):
                method_end = i
                break
        
        if method_end == -1:
            method_end = len(lines)  # Fin du fichier
        
        # Remplacer la méthode par la version corrigée
        corrected_method = [
            '    def show_signal_quality(self):\n',
            '        data = self.get_network_data()\n',
            '        message = f"Analyse du signal WiFi:\\n\\n"\n',
            '        \n',
            '        if self.status == "Excellent":\n',
            '            message += f"✅ Signal: Excellent ({data[\'signal_percent\']}%, RSSI: {data[\'rssi\']} dBm)\\n"\n',
            '        elif self.status == "Bon":\n',
            '            message += f"⚠️ Signal: Acceptable ({data[\'signal_percent\']}%, RSSI: {data[\'rssi\']} dBm)\\n"\n',
            '        else:\n',
            '            message += f"🛑 Signal: Faible ({data[\'signal_percent\']}%, RSSI: {data[\'rssi\']} dBm)\\n"\n',
            '        \n',
            '        message += f"\\nPoint d\'accès: {data[\'bssid\']}\\n"\n',
            '        message += f"Canal: {data[\'channel\']} ({data[\'band\']})\\n"\n',
            '        message += f"Type de radio: {data[\'radio_type\']}\\n"\n',
            '        message += f"Débit: {data[\'rx_speed\']} / {data[\'tx_speed\']} Mbps\\n"\n',
            '        \n',
            '        if data[\'ping\'] > 100:\n',
            '            message += f"🛑 Ping élevé: {data[\'ping\']} ms > 100 ms\\n"\n',
            '        else:\n',
            '            message += f"✅ Ping: {data[\'ping\']} ms\\n"\n',
            '        \n',
            '        message += "\\nRecommandations:\\n"\n',
            '        if self.status == "Excellent":\n',
            '            message += "• Emplacement optimal pour les AMR\\n"\n',
            '            message += "• Continuez sur cette trajectoire\\n"\n',
            '        elif self.status == "Bon":\n',
            '            message += "• Emplacement acceptable, mais surveillez les fluctuations\\n"\n',
            '            message += "• Considérez un AP supplémentaire pour plus de fiabilité\\n"\n',
            '        else:\n',
            '            message += "• Zone problématique pour les AMR - Risque de déconnexion\\n"\n',
            '            message += "• Vérifiez la distance avec l\'AP et les obstacles\\n"\n',
            '            message += "• Installation d\'un AP supplémentaire recommandée\\n"\n',
            '            message += "• Assurez une meilleure couverture avec chevauchement d\'APs\\n"\n',
            '            \n',
            '        messagebox.showinfo("Analyse du signal", message)\n',
            '\n'
        ]
        
        # Construire le nouveau contenu du fichier
        new_lines = lines[:method_start] + corrected_method + lines[method_end:]
        
        # Écrire le fichier corrigé
        with open('main.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print("Fichier main.py corrigé avec succès!")
        return True
    
    except Exception as e:
        print(f"Erreur lors de la correction: {e}")
        return False

if __name__ == "__main__":
    fix_main_py()