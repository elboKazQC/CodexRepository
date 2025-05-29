import os
import json
import logging
import subprocess
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
import platform
import re

@dataclass
class WifiSample:
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
    raw_data: Dict = None
    ping_latency: float = -1.0
    jitter: float = 0.0
    ping_target: str = ""

    @classmethod
    def from_powershell_data(
        cls, data: Dict, prev_latency: Optional[float] = None
    ) -> 'WifiSample':
        """Crée un échantillon à partir des données PowerShell."""

        signal_str = data.get('SignalStrength', '0%').replace('%', '')
        quality = int(signal_str) if signal_str.isdigit() else 0

        def _parse_latency(value) -> float:
            """Interpréte la latence renvoyée par PowerShell."""
            try:
                if isinstance(value, str):
                    clean = value.strip().lower().replace('ms', '').replace('<', '')
                    return float(clean)
                return float(value)
            except (ValueError, TypeError):
                return -1.0

        latency = _parse_latency(data.get('PingLatency', -1))
        jitter = 0.0
        if prev_latency is not None and latency >= 0 and prev_latency >= 0:
            jitter = abs(latency - prev_latency)

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
            ping_latency=latency,
            jitter=jitter,
            raw_data=data
        )

class WifiCollector:
    def __init__(self, script_path: str = None):
        self.script_path = script_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wifi_monitor.ps1')
        self.is_collecting = False
        self.samples: List[WifiSample] = []
        self.error_count = 0
        self.max_errors = 5
        self.logger = self._setup_logging()
        self.last_latency: Optional[float] = None
        self.latency_history: List[float] = []
        self.ping_target: str = ""

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

    def _detect_ping_target(self) -> str:
        """Tente de détecter la gateway par d\xE9faut, sinon retourne DNS Google."""
        try:
            if platform.system().lower().startswith('win'):
                output = subprocess.check_output(["route", "print", "0.0.0.0"], text=True, encoding='latin1')
                match = re.search(r"0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)", output)
                if match:
                    return match.group(1)
            else:
                output = subprocess.check_output(["ip", "route", "show", "default"], text=True)
                match = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", output)
                if match:
                    return match.group(1)
        except Exception as e:
            self.logger.debug(f"Impossible de d\xE9tecter la gateway: {e}")
        return "8.8.8.8"

    def _perform_ping(self, target: str) -> float:
        """R\xE9alise un ping non bloquant vers la cible."""
        try:
            if platform.system().lower().startswith('win'):
                cmd = ["ping", "-n", "1", "-w", "2000", target]
                regex = r"temps[<=](\d+)ms"
            else:
                cmd = ["ping", "-c", "1", "-W", "2", target]
                regex = r"time[<=](\d+\.?\d*) ms"

            output = subprocess.check_output(cmd, text=True, encoding='latin1', stderr=subprocess.DEVNULL)
            match = re.search(regex, output)
            if match:
                return float(match.group(1))
        except Exception as e:
            self.logger.debug(f"Ping failed: {e}")
        return -1.0

    def _update_jitter(self, latency: float) -> float:
        """Calcule le jitter moyen sur une fen\xEAtre glissante."""
        if latency < 0:
            return 0.0
        self.latency_history.append(latency)
        if len(self.latency_history) > 20:
            self.latency_history.pop(0)
        if len(self.latency_history) < 2:
            return 0.0
        diffs = [abs(self.latency_history[i] - self.latency_history[i - 1]) for i in range(1, len(self.latency_history))]
        return sum(diffs) / len(diffs)

    def start_collection(self) -> bool:
        """Démarre la collecte WiFi"""
        try:
            if not os.path.exists(self.script_path):
                raise FileNotFoundError(f"Script PowerShell introuvable: {self.script_path}")

            self.logger.info("Démarrage de la collecte WiFi")
            self.error_count = 0
            self.is_collecting = True
            self.samples = []
            self.latency_history = []
            self.ping_target = self._detect_ping_target()
            self.logger.info(f"Cible de ping utilisée: {self.ping_target}")
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage de la collecte: {str(e)}")
            return False

    def collect_sample(self) -> Optional[WifiSample]:
        """Collecte un échantillon de données WiFi via PowerShell"""
        if not self.is_collecting:
            return None

        try:
            # Exécute le script PowerShell
            result = subprocess.run(
                ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', self.script_path],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse le JSON retourné
            data = json.loads(result.stdout)

            # Si nous sommes connectés, créer l'échantillon
            if data.get('Status') == 'Connected':
                sample = WifiSample.from_powershell_data(data)

                # Mesurer la latence si nécessaire
                latency = sample.ping_latency
                if latency < 0:
                    latency = self._perform_ping(self.ping_target)
                sample.ping_latency = latency

                # Calculer le jitter moyen
                sample.jitter = self._update_jitter(latency)
                sample.ping_target = self.ping_target

                self.last_latency = latency
                self.samples.append(sample)
                if len(self.samples) % 10 == 0:
                    self.logger.debug(f"{len(self.samples)} échantillons collectés")
                self.error_count = 0  # Réinitialise le compteur d'erreurs
                self.logger.debug(f"Échantillon collecté: {sample.ssid} - {sample.signal_strength}dBm")
                return sample
            else:
                self.logger.warning(f"Pas de connexion WiFi: {data.get('Status')}")
                return None

        except subprocess.CalledProcessError as e:
            self.error_count += 1
            self.logger.error(f"Erreur lors de l'exécution du script PowerShell: {e}")
            if self.error_count >= self.max_errors:
                self.logger.critical("Trop d'erreurs consécutives, arrêt de la collecte")
                self.stop_collection()
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Erreur de parsing JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erreur inattendue: {e}")
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
        """Arrête la collecte et retourne les échantillons collectés"""
        self.logger.info("Arrêt de la collecte WiFi")
        self.is_collecting = False
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
