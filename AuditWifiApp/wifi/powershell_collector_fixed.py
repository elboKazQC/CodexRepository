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
        if self.collection_thread:
            self.collection_thread.join()

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
            }, f, indent=2)

        return filepath

    def _collection_loop(self):
        """Boucle de collecte des données"""
        while self.is_collecting:
            data = self.get_wifi_data()
            if data:
                # Ajouter timestamp
                data['timestamp'] = datetime.now().isoformat()
                self.session_data.append(data)

                # Appeler le callback si défini
                if self.data_callback:
                    self.data_callback(data)

            time.sleep(self.collection_interval)

    def get_wifi_data(self) -> Optional[Dict]:
        """
        Exécute le script PowerShell pour obtenir les données WiFi
        """
        try:
            # Vérifier que le script existe
            if not os.path.exists(self.script_path):
                print(f"ERREUR: Script PowerShell non trouvé: {self.script_path}")
                return None

            print(f"DEBUG: Chemin du script PowerShell: {self.script_path}")

            # Exécuter Get-WifiStatus du script PowerShell
            command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ". \'{self.script_path}\'; Get-WifiStatus | ConvertTo-Json"'
            print(f"DEBUG: Commande PowerShell: {command}")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10  # Timeout de 10 secondes
            )

            if result.returncode != 0:
                print(f"ERREUR PowerShell (code {result.returncode}): {result.stderr}")
                return None

            print("DEBUG: Script PowerShell exécuté avec succès")

            # Convertir la sortie JSON en dictionnaire
            try:
                # Afficher les premiers caractères de la sortie pour debug
                print(f"DEBUG: Début de la sortie PowerShell: {result.stdout[:100]}...")

                wifi_data = json.loads(result.stdout)
                print(f"DEBUG: Données WiFi récupérées avec succès: {list(wifi_data.keys())}")
                return wifi_data
            except json.JSONDecodeError as je:
                print(f"ERREUR décodage JSON: {je}")
                print(f"SORTIE brute: {result.stdout}")
                return None

        except subprocess.TimeoutExpired:
            print("ERREUR: Timeout lors de l'exécution du script PowerShell")
            return None
        except Exception as e:
            print(f"ERREUR lors de la collecte WiFi: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
