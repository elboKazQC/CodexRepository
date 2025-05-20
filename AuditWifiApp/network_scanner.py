import subprocess
import re
import os

def percentage_to_dbm(percentage):
    """Convertit un pourcentage de signal en dBm (approximation)"""
    # Une approximation basée sur l'échelle généralement utilisée
    if percentage >= 100:
        return -30
    elif percentage >= 80:
        return -50
    elif percentage >= 60:
        return -60
    elif percentage >= 40:
        return -67
    elif percentage >= 20:
        return -75
    else:
        return -85

def calculate_channel_from_frequency(frequency):
    """Calcule le numéro de canal Wi-Fi à partir de la fréquence en MHz"""
    # Canaux 2.4 GHz (2412-2484 MHz)
    if 2412 <= frequency <= 2484:
        if frequency == 2484:  # Canal 14 spécifique (Japon uniquement)
            return 14
        elif frequency == 2407:  # Canal 0 (rare)
            return 0
        elif 2412 <= frequency <= 2472:  # Canaux 1-13
            return (frequency - 2412) // 5 + 1
        # Fallback pour les cas limites
        return int((frequency - 2407) / 5)
    
    # Canaux 5 GHz (de nombreuses bandes)
    elif 5170 <= frequency <= 5825:
        # UNII-1 (36-48)
        if 5170 <= frequency <= 5240:
            return (frequency - 5170) // 5 + 34  # Commence au canal 36 (-2 d'offset)
        # UNII-2 (52-64)
        elif 5250 <= frequency <= 5330:
            return (frequency - 5250) // 5 + 52
        # UNII-2e (100-144)
        elif 5490 <= frequency <= 5710:
            return (frequency - 5490) // 5 + 100
        # UNII-3 (149-165)
        elif 5735 <= frequency <= 5835:
            return (frequency - 5735) // 5 + 149
        # Fallback pour les cas limites dans la bande 5 GHz
        return ((frequency - 5000) // 5) // 5 * 4 + 32
    
    # Bande 6 GHz (nouveaux canaux Wi-Fi 6E)
    elif 5945 <= frequency <= 7125:
        # Simplification: canal = (freq - 5950) / 5 + 1
        return (frequency - 5950) // 5 + 1
    
    # Si on ne peut pas déterminer le canal
    return 0  # Canal inconnu

def frequency_to_band(frequency):
    """Détermine la bande de fréquence (2.4 GHz, 5 GHz ou 6 GHz) à partir de la fréquence en MHz"""
    if 2400 <= frequency <= 2500:
        return "2.4 GHz"
    elif 5100 <= frequency <= 5900:
        return "5 GHz"
    elif 5945 <= frequency <= 7125:
        return "6 GHz"
    return "Inconnu"

def detect_wifi_driver_info():
    """Détecte les informations sur les pilotes Wi-Fi et les interfaces"""
    try:
        # Utiliser PowerShell pour obtenir des informations détaillées sur les pilotes et interfaces Wi-Fi
        ps_command = "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*wireless*' -or $_.InterfaceDescription -like '*wifi*' -or $_.InterfaceDescription -like '*wi-fi*'} | Format-List Name,InterfaceDescription,DriverVersion,DriverProvider,Status"
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Obtenir également les informations sur l'interface Wi-Fi active
        wifi_status_command = "netsh wlan show interfaces"
        wifi_status = subprocess.run(
            ["cmd", "/c", wifi_status_command],
            capture_output=True,
            text=True,
            check=False,
            encoding='utf-8'
        )
        
        output = "=== Adaptateurs Wi-Fi détectés ===\n"
        if result.returncode == 0 and result.stdout.strip():
            output += result.stdout + "\n"
        else:
            output += "Aucun adaptateur Wi-Fi trouvé via PowerShell.\n\n"
            
        output += "=== État des interfaces Wi-Fi ===\n"
        if wifi_status.returncode == 0 and wifi_status.stdout.strip():
            output += wifi_status.stdout
        else:
            output += "Impossible d'obtenir l'état des interfaces Wi-Fi.\n"
            
        return output
    except Exception as e:
        return f"Erreur lors de la détection des informations Wi-Fi: {str(e)}"

def get_channel_from_bssid(bssid):
    """Obtient les détails d'un point d'accès spécifique, y compris son canal et sa fréquence."""
    try:
        # Utiliser netsh wlan show network pour obtenir les détails plus précis d'un BSSID spécifique
        result = subprocess.run(
            ["netsh", "wlan", "show", "network", "bssid=" + bssid],
            capture_output=True,
            text=True,
            check=False,
            encoding='utf-8'
        )
        
        channel = 0
        frequency = "Inconnu"
        freq_mhz = 0
        
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            for line in lines:
                line = line.strip()
                
                # Extraction du canal
                if "Channel" in line and ":" in line:
                    channel_parts = line.split(":", 1)
                    if len(channel_parts) > 1:
                        try:
                            channel = int(channel_parts[1].strip())
                        except ValueError:
                            pass
                
                # Extraction de la fréquence
                elif "Frequency" in line and ":" in line:
                    freq_parts = line.split(":", 1)
                    if len(freq_parts) > 1:
                        freq_str = freq_parts[1].strip().lower()
                        
                        # Détecter la bande et obtenir la fréquence en MHz
                        if '2.4' in freq_str or '2,4' in freq_str:
                            frequency = "2.4 GHz"
                            # Estimer la fréquence centrale en MHz en fonction du canal
                            if channel > 0 and channel <= 14:
                                freq_mhz = 2412 + (channel - 1) * 5
                        elif '5' in freq_str:
                            frequency = "5 GHz"
                            # Estimer la fréquence centrale en MHz pour la bande 5 GHz
                            if channel >= 36:
                                freq_mhz = 5170 + (channel - 36) * 5
        
        return channel, frequency, freq_mhz
    
    except Exception:
        return 0, "Inconnu", 0

def scan_wifi():
    """Scanne les réseaux Wi-Fi disponibles en utilisant netsh et retourne une liste de résultats."""
    try:
        # Méthode 1: Commande NETSH principale pour obtenir les réseaux Wi-Fi
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'  # Utiliser UTF-8 pour gérer correctement les caractères spéciaux
        )

        networks = []
        current_network = {}
        current_bssid = None
        lines = result.stdout.splitlines()
        
        # Première analyse pour extraire les informations de base
        for i, line in enumerate(lines):
            line = line.strip()
            
            # SSID (nom du réseau)
            if "SSID" in line and ":" in line and not "BSSID" in line:
                if current_network and current_bssid:  # Si on a déjà un réseau en cours, on l'ajoute
                    networks.append(current_network.copy())
                
                ssid_parts = line.split(":", 1)
                if len(ssid_parts) > 1:
                    ssid = ssid_parts[1].strip()
                    current_network = {"ssid": ssid}
                    current_bssid = None
            
            # BSSID (adresse MAC du point d'accès)
            elif "BSSID" in line and ":" in line:
                bssid_parts = line.split(":", 1)
                if len(bssid_parts) > 1:
                    current_bssid = bssid_parts[1].strip()
                    current_network["bssid"] = current_bssid
            
            # Signal
            elif "Signal" in line and ":" in line and current_bssid:
                signal_parts = line.split(":", 1)
                if len(signal_parts) > 1:
                    signal_str = signal_parts[1].strip()
                    if "%" in signal_str:
                        try:
                            # Convertir le pourcentage en dBm
                            signal_percent = int(signal_str.replace("%", ""))
                            signal_dbm = percentage_to_dbm(signal_percent)
                            current_network["signal"] = signal_dbm
                            current_network["signal_percent"] = f"{signal_percent}%"
                        except ValueError:
                            current_network["signal"] = -65  # Valeur par défaut
                            current_network["signal_percent"] = signal_str
            
            # Canal
            elif "Channel" in line and ":" in line and current_bssid:
                channel_parts = line.split(":", 1)
                if len(channel_parts) > 1:
                    try:
                        channel = int(channel_parts[1].strip())
                        if channel > 0:  # Si on a pu extraire un canal valide
                            current_network["channel"] = channel
                    except ValueError:
                        pass  # On essaiera de calculer le canal plus tard
            
            # Radio type & Frequency
            elif any(x in line for x in ["Radio type", "Band", "Frequency"]) and ":" in line and current_bssid:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    value = parts[1].strip().lower()
                    
                    # Essayer d'extraire la fréquence
                    freq_match = re.search(r'(\d+)(\.\d+)?\s*ghz|(\d+)\s*mhz', value)
                    if freq_match:
                        if 'ghz' in value:
                            if '2.4' in value or '2,4' in value:
                                current_network["frequency"] = "2.4 GHz"
                                if "channel" not in current_network:
                                    # Canaux par défaut pour 2.4 GHz
                                    current_network["channel"] = 1  # On suppose canal 1 par défaut
                            elif '5' in value:
                                current_network["frequency"] = "5 GHz"
                                if "channel" not in current_network:
                                    # Canaux par défaut pour 5 GHz
                                    current_network["channel"] = 36  # On suppose canal 36 par défaut
                        elif 'mhz' in value:
                            try:
                                # Extraire la valeur exacte de la fréquence
                                freq_val = int(re.search(r'(\d+)\s*mhz', value).group(1))
                                current_network["frequency_mhz"] = freq_val
                                current_network["frequency"] = frequency_to_band(freq_val)
                                
                                if "channel" not in current_network:
                                    current_network["channel"] = calculate_channel_from_frequency(freq_val)
                            except (ValueError, AttributeError):
                                pass
                    
                    # Si on n'a toujours pas de fréquence mais qu'on a des indices dans le type radio
                    if "frequency" not in current_network:
                        if any(x in value for x in ["802.11b", "802.11g", "802.11n"]):
                            current_network["frequency"] = "2.4 GHz"
                            if "channel" not in current_network:
                                current_network["channel"] = 1  # Canal par défaut
                        elif any(x in value for x in ["802.11a", "802.11ac"]):
                            current_network["frequency"] = "5 GHz"
                            if "channel" not in current_network:
                                current_network["channel"] = 36  # Canal par défaut
        
        # Ajouter le dernier réseau s'il existe
        if current_network and current_bssid:
            networks.append(current_network)

        # Méthode 2: Utiliser netsh wlan show networks bssid=X pour obtenir plus de détails
        # Cette méthode est plus précise pour les canaux et les fréquences
        for network in networks:
            # Si on n'a pas de canal valide ou de fréquence valide, essayer d'obtenir plus de détails
            if "channel" not in network or network["channel"] == 0 or "frequency" not in network or network["frequency"] == "Inconnu":
                if "bssid" in network:
                    try:
                        channel, frequency, freq_mhz = get_channel_from_bssid(network["bssid"])
                        if channel > 0:
                            network["channel"] = channel
                        if frequency != "Inconnu":
                            network["frequency"] = frequency
                        if freq_mhz > 0:
                            network["frequency_mhz"] = freq_mhz
                    except Exception:
                        pass  # Ignorer les erreurs sur cette méthode de secours

        # Méthode 3: Essayer d'utiliser la commande netsh wlan show interface
        if networks:
            try:
                # Récupérer des informations sur l'interface actuellement connectée
                interface_result = subprocess.run(
                    ["netsh", "wlan", "show", "interface"],
                    capture_output=True,
                    text=True,
                    check=False,
                    encoding='utf-8'
                )
                
                if interface_result.returncode == 0:
                    connected_bssid = None
                    connected_channel = 0
                    connected_freq = "Inconnu"
                    
                    lines = interface_result.stdout.splitlines()
                    for line in lines:
                        line = line.strip()
                        
                        # BSSID connecté
                        if "BSSID" in line and ":" in line:
                            bssid_parts = line.split(":", 1)
                            if len(bssid_parts) > 1:
                                connected_bssid = bssid_parts[1].strip()
                        
                        # Canal
                        elif "Channel" in line and ":" in line:
                            channel_parts = line.split(":", 1)
                            if len(channel_parts) > 1:
                                try:
                                    connected_channel = int(channel_parts[1].strip())
                                except ValueError:
                                    pass
                        
                        # Type de radio (pour la fréquence)
                        elif "Radio type" in line and ":" in line:
                            radio_parts = line.split(":", 1)
                            if len(radio_parts) > 1:
                                radio_type = radio_parts[1].strip().lower()
                                if "802.11n" in radio_type or "802.11g" in radio_type or "802.11b" in radio_type:
                                    connected_freq = "2.4 GHz"
                                elif "802.11a" in radio_type or "802.11ac" in radio_type:
                                    connected_freq = "5 GHz"
                    
                    # Utiliser les informations de l'interface connectée pour mettre à jour le réseau correspondant
                    if connected_bssid:
                        for network in networks:
                            if network.get("bssid") == connected_bssid:
                                if connected_channel > 0 and (network.get("channel", 0) == 0):
                                    network["channel"] = connected_channel
                                if connected_freq != "Inconnu" and network.get("frequency", "Inconnu") == "Inconnu":
                                    network["frequency"] = connected_freq
            except Exception:
                pass  # Ignorer les erreurs de cette méthode
        
        # Méthode 4: Utiliser la commande netsh wlan show all pour des informations détaillées
        if networks:
            try:
                # Cette commande montre tous les détails des interfaces et réseaux
                all_result = subprocess.run(
                    ["netsh", "wlan", "show", "all"],
                    capture_output=True,
                    text=True,
                    check=False,
                    encoding='utf-8'
                )
                
                if all_result.returncode == 0:
                    lines = all_result.stdout.splitlines()
                    current_bssid = None
                    current_channel = 0
                    current_freq = "Inconnu"
                    
                    for line in lines:
                        line = line.strip()
                        
                        # BSSID
                        if "BSSID" in line and ":" in line:
                            bssid_parts = line.split(":", 1)
                            if len(bssid_parts) > 1:
                                current_bssid = bssid_parts[1].strip()
                        
                        # Canal
                        elif "Channel" in line and ":" in line:
                            channel_parts = line.split(":", 1)
                            if len(channel_parts) > 1:
                                try:
                                    current_channel = int(channel_parts[1].strip())
                                except ValueError:
                                    pass
                        
                        # Fréquence
                        elif any(x in line for x in ["Frequency", "Band"]) and ":" in line:
                            freq_parts = line.split(":", 1)
                            if len(freq_parts) > 1:
                                freq_str = freq_parts[1].strip().lower()
                                if "2.4" in freq_str or "2,4" in freq_str:
                                    current_freq = "2.4 GHz"
                                elif "5" in freq_str:
                                    current_freq = "5 GHz"
                        
                        # Si on a toutes les infos, mettre à jour le réseau correspondant
                        if current_bssid and current_channel > 0:
                            for network in networks:
                                if network.get("bssid") == current_bssid:
                                    if network.get("channel", 0) == 0:
                                        network["channel"] = current_channel
                                    if network.get("frequency", "Inconnu") == "Inconnu" and current_freq != "Inconnu":
                                        network["frequency"] = current_freq
                            
                            # Réinitialiser pour le prochain réseau
                            current_bssid = None
                            current_channel = 0
                            current_freq = "Inconnu"
            except Exception:
                pass  # Ignorer les erreurs de cette méthode

        # S'assurer que tous les réseaux ont des valeurs par défaut raisonnables
        for network in networks:
            # S'assurer que chaque réseau a un canal attribué
            if "channel" not in network or network["channel"] == 0:
                # Attribuer un canal par défaut selon la bande
                if network.get("frequency") == "5 GHz":
                    network["channel"] = 36
                else:
                    network["channel"] = 1
            
            # S'assurer que chaque réseau a une fréquence attribuée
            if "frequency" not in network or network["frequency"] == "Inconnu":
                # Déduire la bande à partir du canal
                if network.get("channel", 0) >= 36:
                    network["frequency"] = "5 GHz"
                else:
                    network["frequency"] = "2.4 GHz"
                    
        # Si on n'a pas trouvé de réseaux avec netsh, essayer iwlist sur WSL si disponible
        if not networks and os.path.exists("C:\\Windows\\System32\\wsl.exe"):
            try:
                # Essayer d'abord avec iwlist
                wsl_result = subprocess.run(
                    ["wsl", "iwlist", "wlan0", "scan"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10
                )
                
                # Si iwlist ne fonctionne pas, essayer iw
                if wsl_result.returncode != 0:
                    wsl_result = subprocess.run(
                        ["wsl", "iw", "dev", "wlan0", "scan"],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10
                    )
                
                # Analyse des résultats de iwlist/iw
                current_network = {}
                for line in wsl_result.stdout.splitlines():
                    line = line.strip()
                    
                    if "Cell" in line and "Address:" in line:
                        if current_network:
                            networks.append(current_network.copy())
                        current_network = {}
                        bssid = re.search(r'Address:\s*([0-9A-Fa-f:]+)', line)
                        if bssid:
                            current_network["bssid"] = bssid.group(1)
                    
                    elif "ESSID:" in line:
                        ssid = re.search(r'ESSID:"([^"]*)"', line)
                        if ssid:
                            current_network["ssid"] = ssid.group(1)
                    
                    elif "Quality=" in line:
                        signal = re.search(r'Signal level=(-\d+) dBm', line)
                        if signal:
                            current_network["signal"] = int(signal.group(1))
                            # Calculer pourcentage approximatif
                            if current_network["signal"] >= -50:
                                percent = 100
                            elif current_network["signal"] >= -80:
                                percent = 100 - ((current_network["signal"] + 50) * 2)
                            else:
                                percent = 0
                            current_network["signal_percent"] = f"{percent}%"
                    
                    elif "Frequency:" in line:
                        freq = re.search(r'Frequency:(\d+\.\d+) GHz', line)
                        channel = re.search(r'Channel (\d+)', line)
                        
                        if freq:
                            freq_val = float(freq.group(1))
                            if 2.4 <= freq_val <= 2.5:
                                current_network["frequency"] = "2.4 GHz"
                                # Calculer la fréquence en MHz
                                current_network["frequency_mhz"] = int(freq_val * 1000)
                            elif 5.0 <= freq_val <= 5.9:
                                current_network["frequency"] = "5 GHz"
                                # Calculer la fréquence en MHz
                                current_network["frequency_mhz"] = int(freq_val * 1000)
                            else:
                                current_network["frequency"] = f"{freq_val} GHz"
                        
                        if channel:
                            current_network["channel"] = int(channel.group(1))
                        elif "frequency_mhz" in current_network:
                            # Calculer le canal à partir de la fréquence
                            current_network["channel"] = calculate_channel_from_frequency(current_network["frequency_mhz"])
                
                # Ajouter le dernier réseau
                if current_network:
                    networks.append(current_network)
            
            except Exception:
                pass  # Ignorer les erreurs WSL

        # Méthode de dernier recours: Utiliser des outils PowerShell si disponibles
        if not networks:
            try:
                # Utiliser Get-NetAdapter et Get-NetConnectionProfile pour obtenir des informations sur l'interface connectée
                ps_command = "Get-NetAdapter | Where-Object {$_.Status -eq 'Up' -and $_.InterfaceDescription -like '*wireless*'} | Format-List Name,InterfaceDescription,MacAddress"
                ps_result = subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if ps_result.returncode == 0 and ps_result.stdout.strip():
                    # On a trouvé au moins une interface Wi-Fi active
                    # Essayer d'obtenir des informations sur la connexion actuelle
                    conn_command = "Get-NetConnectionProfile | Where-Object {$_.InterfaceAlias -like '*Wi-Fi*'} | Format-List Name,NetworkCategory,InterfaceAlias"
                    conn_result = subprocess.run(
                        ["powershell", "-Command", conn_command],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    # Créer un réseau minimal avec les informations disponibles
                    if conn_result.returncode == 0 and conn_result.stdout.strip():
                        lines = conn_result.stdout.splitlines()
                        ssid = "Inconnu"
                        
                        for line in lines:
                            if "Name" in line and ":" in line:
                                name_parts = line.split(":", 1)
                                if len(name_parts) > 1:
                                    ssid = name_parts[1].strip()
                        
                        # Créer un réseau avec les informations minimales
                        if ssid != "Inconnu":
                            network = {
                                "ssid": ssid,
                                "bssid": "00:00:00:00:00:00",  # BSSID inconnu
                                "signal": -65,  # Signal moyen par défaut
                                "signal_percent": "50%",  # Pourcentage moyen par défaut
                                "channel": 1,  # Canal par défaut pour 2.4 GHz
                                "frequency": "2.4 GHz"  # Bande par défaut
                            }
                            networks.append(network)
            except Exception:
                pass  # Ignorer les erreurs PowerShell

        return networks

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Erreur lors de l'exécution de netsh: {e}")
    except FileNotFoundError:
        # netsh not available on this system
        return []
    except Exception as e:
        raise RuntimeError(f"Erreur inattendue: {str(e)}")
