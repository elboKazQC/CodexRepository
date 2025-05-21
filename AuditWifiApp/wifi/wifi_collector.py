import os
import json
import logging
import subprocess
import time
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
from queue import Queue, Empty
from threading import Thread

@dataclass
class WifiSample:
    """Représente une mesure WiFi provenant du script PowerShell."""
    timestamp: str
    ssid: str
    bssid: str
    signal_strength: int  # en dBm
    quality: int  # en %
    channel: int
    band: str
    status: str
    transmit_rate: str
    receive_rate: str
    raw_data: Dict
    location_tag: str = ""

    @classmethod
    def from_powershell_data(cls, data: Dict, location_tag: str = "") -> 'WifiSample':
        """Crée un échantillon à partir des données PowerShell"""
        # Convertit le pourcentage en valeur numérique
        signal_str = data.get('SignalStrength', '0%').replace('%', '')
        quality = int(signal_str) if signal_str.isdigit() else 0

        return cls(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            ssid=data.get('SSID', 'N/A'),
            bssid=data.get('BSSID', '00:00:00:00:00:00'),
            signal_strength=int(data.get('SignalStrengthDBM', -100)),
            quality=quality,
            channel=int(data.get('Channel', 0)),
            band=data.get('Band', 'N/A'),
            status=data.get('Status', 'Disconnected'),
            transmit_rate=data.get('TransmitRate', '0 Mbps'),
            receive_rate=data.get('ReceiveRate', '0 Mbps'),
            raw_data=data,
            location_tag=location_tag
        )

class WifiCollector:
    """Collecte des échantillons WiFi via un script PowerShell exécuté en tâche de fond."""
    def __init__(self, script_path: str = None):
        self.script_path = script_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'wifi_monitor.ps1'
        )
        self.is_collecting = False
        self.samples: List[WifiSample] = []
        self.current_location_tag: str = ""
        self.error_count = 0
        self.max_errors = 5
        self.collection_interval = 1.0
        self._queue: Queue[WifiSample] = Queue()
        self.collection_thread: Optional[Thread] = None
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configure le système de journalisation avec rotation des fichiers"""
        logger = logging.getLogger('WifiCollector')
        logger.setLevel(logging.DEBUG)

        # Nettoyage des handlers existants
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Handler pour la console avec couleurs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Handler pour le fichier avec rotation
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'wifi_collector.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        return logger

    def _collection_loop(self) -> None:
        """Thread loop executing the PowerShell script periodically."""
        while self.is_collecting:
            try:
                result = subprocess.run(
                    ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', self.script_path],
                    capture_output=True,
                    text=True,
                    check=True
                )

                data = json.loads(result.stdout)

                if data.get('Status') == 'Connected':
                    sample = WifiSample.from_powershell_data(
                        data, self.current_location_tag
                    )
                    self.samples.append(sample)
                    self._queue.put(sample)
                    self.error_count = 0
                    self.logger.debug(
                        "Échantillon collecté: %s - %sdBm", sample.ssid, sample.signal_strength
                    )
                else:
                    self.logger.warning("Pas de connexion WiFi: %s", data.get('Status'))

            except subprocess.CalledProcessError as e:
                self._handle_error(
                    f"Erreur lors de l'exécution du script PowerShell: {e}"
                )
            except json.JSONDecodeError as e:
                self._handle_error(f"Erreur de parsing JSON: {e}")
            except Exception as e:  # pragma: no cover - unexpected errors
                self._handle_error(f"Erreur inattendue: {e}")

            time.sleep(self.collection_interval)

    def start_collection(self, location_tag: str = "") -> bool:
        """Démarre la collecte WiFi"""
        try:
            if not os.path.exists(self.script_path):
                raise FileNotFoundError(f"Script PowerShell introuvable: {self.script_path}")

            self.logger.info("Démarrage de la collecte WiFi")
            self.current_location_tag = location_tag
            self.error_count = 0
            self.is_collecting = True
            self.samples = []
            self._queue = Queue()
            self.collection_thread = Thread(target=self._collection_loop, daemon=True)
            self.collection_thread.start()
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage de la collecte: {str(e)}")
            return False

    def set_location_tag(self, tag: str) -> None:
        """Met à jour le tag de localisation utilisé pour les prochains échantillons."""
        self.current_location_tag = tag

    def collect_sample(self) -> Optional[WifiSample]:
        """Retourne le dernier échantillon mis en file."""
        if not self.is_collecting:
            return None

        try:
            return self._queue.get_nowait()
        except Empty:
            return None

    def _handle_error(self, message: str) -> None:
        """Gère les erreurs de collecte"""
        self.error_count += 1
        self.logger.error(f"{message} ({self.error_count}/{self.max_errors})")

        if self.error_count >= self.max_errors:
            self.logger.critical(
                "Nombre maximum d'erreurs atteint, arrêt de la collecte"
            )
            self.stop_collection()

    def stop_collection(self) -> List[WifiSample]:
        """Arrête la collecte et retourne les échantillons collectés."""
        self.logger.info("Arrêt de la collecte WiFi")
        self.is_collecting = False
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=2.0)
        return self.samples

    def get_latest_sample(self) -> Optional[WifiSample]:
        """Retourne le dernier échantillon collecté"""
        return self.samples[-1] if self.samples else None

    def export_samples(self, filename: str = None) -> str:
        """Exporte les échantillons au format JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wifi_samples_{timestamp}.json"

        export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(export_dir, exist_ok=True)
        export_path = os.path.join(export_dir, filename)

        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(
                    [vars(sample) for sample in self.samples],
                    f,
                    indent=2,
                    ensure_ascii=False
                )
            self.logger.info(f"Données exportées vers {export_path}")
            return export_path
        except Exception as e:
            self.logger.error(f"Erreur lors de l'export: {str(e)}")
            return ""
