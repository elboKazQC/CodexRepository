"""
Interface avec le script PowerShell de collecte WiFi
"""
import subprocess
import json
from typing import Optional, Dict, List
import os
from datetime import datetime
import threading
import time

class PowerShellWiFiCollector:
    def __init__(self):
        self.script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wifi_monitor.ps1')
        self.is_collecting = False
        self.collection_thread = None
        self.data_callback = None
        self.collection_interval = 1.0  # Intervalle en secondes
        self.current_session = None
        self.session_data = []

    def get_wifi_data(self) -> Optional[Dict]:
        """Exécute le script PowerShell pour obtenir les données WiFi"""
        try:
            # Vérifier que le script existe
            if not os.path.exists(self.script_path):
                print(f"ERREUR: Script PowerShell non trouvé: {self.script_path}")
                return None

            # Exécuter Get-WifiStatus du script PowerShell
            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", self.script_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,  # Utilise l'encodage par défaut du système
                timeout=10
            )

            if result.returncode != 0:
                print(f"ERREUR PowerShell (code {result.returncode}): {result.stderr}")
                return None

            # Nettoyer les caractères non-JSON
            output = result.stdout.strip()
            if not output:
                print("ERREUR: Sortie PowerShell vide")
                return None

            # Parse le JSON
            wifi_data = json.loads(output)
            if not isinstance(wifi_data, dict):
                print(f"ERREUR: Format de données inattendu: {type(wifi_data)}")
                return None

            # Normaliser les noms des champs
            signal_raw = wifi_data.get("SignalStrength", wifi_data.get("Signal", 0))
            signal_percent = int(str(signal_raw).replace("%", ""))
            signal_dbm = wifi_data.get("SignalStrengthDBM")

            if signal_dbm is None:
                signal_dbm = -100 + signal_percent * 0.5
            else:
                try:
                    signal_dbm = int(signal_dbm)
                except ValueError:
                    signal_dbm = -100 + signal_percent * 0.5

            # Retourner les données normalisées
            normalized_data = {
                "SSID": wifi_data.get("SSID", "N/A"),
                "BSSID": wifi_data.get("BSSID", "00:00:00:00:00:00"),
                "SignalStrength": f"{signal_percent}%",
                "SignalStrengthDBM": signal_dbm,
                "Channel": wifi_data.get("Channel", "0"),
                "Band": wifi_data.get("Band", "2.4 GHz"),
                "Status": wifi_data.get("Status", "Déconnecté"),
                "TransmitRate": wifi_data.get("TransmitRate", "0 Mbps"),
                "ReceiveRate": wifi_data.get("ReceiveRate", "0 Mbps"),
                "NoiseFloor": wifi_data.get("NoiseFloor", -100),
                "SNR": wifi_data.get("SNR", None)
            }

            return normalized_data

        except subprocess.TimeoutExpired:
            print("ERREUR: Timeout lors de l'exécution du script PowerShell")
            return None
        except json.JSONDecodeError as je:
            print(f"ERREUR décodage JSON: {je}")
            print(f"SORTIE brute: {result.stdout}")
            return None
        except Exception as e:
            print(f"ERREUR lors de la collecte WiFi: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _collection_loop(self):
        """Boucle de collecte des données"""
        error_count = 0
        max_errors = 3

        while self.is_collecting:
            try:
                data = self.get_wifi_data()
                if data:
                    # Reset error counter on success
                    error_count = 0

                    # Add timestamp
                    data['timestamp'] = datetime.now().isoformat()
                    self.session_data.append(data)

                    # Call callback if defined
                    if self.data_callback:
                        try:
                            self.data_callback(data)
                        except Exception as e:
                            print(f"Erreur dans le callback: {str(e)}")

                else:
                    error_count += 1
                    if error_count >= max_errors:
                        print("Erreur: Trop d'échecs consécutifs de collecte, arrêt.")
                        self.stop_collection()
                        break

                time.sleep(self.collection_interval)

            except Exception as e:
                print(f"Erreur dans la boucle de collecte: {str(e)}")
                error_count += 1
                if error_count >= max_errors:
                    print("Erreur: Trop d'erreurs consécutives, arrêt.")
                    self.stop_collection()
                    break

                time.sleep(self.collection_interval * 2)  # Attente plus longue en cas d'erreur

    def start_collection(self, callback=None, interval: float = 1.0):
        """
        Démarre une session de collecte de données WiFi

        Args:
            callback: Fonction appelée avec les données à chaque collecte
            interval: Intervalle entre les collectes en secondes
        """
        if self.is_collecting:
            return False

        self.is_collecting = True
        self.data_callback = callback
        self.collection_interval = interval
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_data = []

        # Démarrer la collecte dans un thread séparé
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()

        return True

    def stop_collection(self) -> List[Dict]:
        """
        Arrête la session de collecte en cours et retourne les données
        """
        if not self.is_collecting:
            return []

        self.is_collecting = False
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=2.0)

        return self.session_data

    def save_session_data(self, directory: str):
        """
        Sauvegarde les données de la session dans un fichier JSON
        """
        if not self.session_data:
            return None

        os.makedirs(directory, exist_ok=True)
        filename = f"wifi_session_{self.current_session}.json"
        filepath = os.path.join(directory, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'session_id': self.current_session,
                'timestamp': datetime.now().isoformat(),
                'measurements': self.session_data
            }, f, indent=2, ensure_ascii=False)

        return filepath
