"""
Collecteur de données WiFi pour l'audit de couverture
"""
import os
import json
import logging
import logging.handlers
import threading
import re
import time
import subprocess
from datetime import datetime
from typing import List, Optional, Dict

from config_manager import ConfigurationManager
from app_config import Constants

from models.measurement_record import WifiMeasurement, PingMeasurement, NetworkStatus
from models.wifi_record import WifiRecord
from wifi.powershell_collector import PowerShellWiFiCollector
from app_config import load_config
from config_manager import ConfigurationManager


# Constantes de configuration
RETRY_CONFIG = {
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 2,  # secondes
    'SCAN_TIMEOUT': 10,  # secondes
    'PING_TIMEOUT': 10,  # secondes
}

# Seuils par défaut pour la qualité WiFi
DEFAULT_WIFI_THRESHOLDS = {
    "signal": {"weak": -70, "critical": -80},
    "packet_loss": {"warning": 10, "critical": 20},
    "latency": {"warning": 100, "critical": 200},
}


def _percent_to_dbm(percent: int) -> int:
    """Convertit un pourcentage de signal en dBm (approximation)"""
    if percent >= 100:
        return -50
    elif percent <= 0:
        return -100
    return int(-100 + (percent / 2))

def _channel_to_frequency_mhz(channel: int) -> int:
    """Convertit un numéro de canal en fréquence MHz"""
    if 1 <= channel <= 14:  # 2.4 GHz
        return 2407 + (channel * 5)
    elif 36 <= channel <= 165:  # 5 GHz
        return 5000 + (channel * 5)
    return 0

class WifiDataCollector:
    """Collecte des données WiFi et les stocke dans des enregistrements."""


    def __init__(self, base_path: str | None = None, config_manager: ConfigurationManager | None = None):
        """Initialise le collecteur avec les paramètres issus de la configuration."""
        self.config_manager = config_manager or ConfigurationManager(path=Constants.CONFIG_PATH)
        cfg = self.config_manager.get_config().get("wifi", {})
        collector_cfg = cfg.get("collector", {})
        self.retry_config = collector_cfg.get("retry", {})
        self.thresholds = cfg.get("thresholds", {})

        self.base_path = base_path or collector_cfg.get("base_path", "logs_moxa")

        self.current_cycle: int = 0
        self.current_zone: str = "Non spécifiée"
        self.current_location_tag: str = ""
        self.is_collecting = False
        self.measurement_lock = threading.Lock()
        if config_manager is None:
            cfg = load_config()
            config_manager = ConfigurationManager(cfg)
        self.config_manager = config_manager
        self.wifi_thresholds = self.config_manager.get_config().get("wifi_thresholds", DEFAULT_WIFI_THRESHOLDS)
        self._setup_logging()
        self.ps_collector = PowerShellWiFiCollector()
        self.records: List[WifiRecord] = []

    def _setup_logging(self):
        """Configure le système de logging"""
        self.logger = logging.getLogger('wifi_collector')
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            # Configure console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # Configure file handler
            os.makedirs(self.base_path, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                os.path.join(self.base_path, 'wifi_collector.log'),
                maxBytes=1024*1024,
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self.logger.debug("Logger configured")

    def _create_wifi_measurement_from_ps(self, wifi_data: Dict) -> Optional[WifiMeasurement]:
        """Crée un objet WifiMeasurement à partir des données PowerShell"""
        try:
            if not wifi_data:
                self.logger.error("Données WiFi vides")
                return None

            # Get required fields with default values
            ssid = str(wifi_data.get('SSID', 'N/A'))
            signal_str = str(wifi_data.get('SignalStrength', '0%'))
            signal_percent = int(signal_str.strip('%') if '%' in signal_str else signal_str)

            # Get signal strength in dBm
            signal_dbm = wifi_data.get('SignalStrengthDBM')
            if signal_dbm is None:
                signal_dbm = int(-100 + (signal_percent * 0.5))
            else:
                signal_dbm = int(float(signal_dbm))

            # Get channel info
            channel_str = str(wifi_data.get('Channel', '0'))
            channel_val = int(channel_str) if channel_str.isdigit() else 0

            # Get band info
            band = str(wifi_data.get('Band', '2.4 GHz'))

            # Get noise floor and SNR
            noise_floor = wifi_data.get('NoiseFloor')
            noise_floor = int(float(noise_floor)) if isinstance(noise_floor, (int, str)) and str(noise_floor).strip('-').replace('.','').isdigit() else None

            snr_value = wifi_data.get('SNR')
            snr_value = int(float(snr_value)) if isinstance(snr_value, (int, str)) and str(snr_value).replace('.','').isdigit() else None

            # Calculate SNR if not provided but we have noise floor
            if snr_value is None and noise_floor is not None:
                snr_value = int(signal_dbm - noise_floor)

            # Calculate frequency from channel
            frequency_mhz = 0
            if channel_val > 0:
                if channel_val <= 13:  # 2.4 GHz band
                    frequency_mhz = 2412 + ((channel_val - 1) * 5)
                else:  # 5 GHz band
                    frequency_mhz = 5170 + ((channel_val - 34) * 5)

            self.logger.debug(f"Création mesure WiFi: SSID={ssid}, Signal={signal_percent}% ({signal_dbm}dBm), Canal={channel_val}")

            # Create measurement
            return WifiMeasurement(
                ssid=ssid,
                bssid=str(wifi_data.get('BSSID', '00:00:00:00:00:00')),
                signal_percent=signal_percent,
                signal_dbm=signal_dbm,
                channel=channel_val,
                band=band,
                frequency=band,
                frequency_mhz=frequency_mhz,
                is_connected=ssid != 'N/A',
                channel_utilization=int(float(str(wifi_data.get('ChannelUtilization', '0')).strip('%'))) / 100,
                noise_floor=noise_floor,
                snr=snr_value
            )

        except Exception as e:
            self.logger.error(f"Erreur lors de la création de la mesure WiFi: {str(e)}", exc_info=True)
            return None

    def start_collection(self, zone: str = "", location_tag: str = "", interval: float = 1.0) -> bool:
        """Démarre la collecte de données WiFi"""
        if self.is_collecting:
            return False

        self.current_zone = zone
        self.current_location_tag = location_tag
        self.is_collecting = True

        # Démarre la collecte PowerShell avec callback
        self.ps_collector.start_collection(
            callback=self._handle_wifi_data,
            interval=interval
        )

        self.logger.info(f"Collection démarrée - Zone: {zone}, Tag: {location_tag}")
        return True

    def stop_collection(self) -> bool:
        """Arrête la collecte de données WiFi"""
        if not self.is_collecting:
            return False

        self.is_collecting = False

        # Récupère et sauvegarde les données de la session
        session_data = self.ps_collector.stop_collection()
        if session_data:
            self.ps_collector.save_session_data(self.base_path)

        self.logger.info("Collection arrêtée")
        return True

    def _handle_wifi_data(self, wifi_data: Dict):
        """Traite les données WiFi reçues du collecteur PowerShell"""
        with self.measurement_lock:
            try:
                timestamp = datetime.fromisoformat(wifi_data['timestamp'])
                wifi_measurement = self._create_wifi_measurement_from_ps(wifi_data)

                if not wifi_measurement:
                    return

                # Créer le ping measurement si disponible
                ping_measurement = None
                if int(wifi_data.get('PingLatency', -1)) >= 0:
                    ping_measurement = PingMeasurement(
                        latency=int(wifi_data['PingLatency']),
                        packet_loss=int(wifi_data.get('PacketLoss', 0))
                    )

                # Créer le record
                record = WifiRecord(
                    timestamp=timestamp,
                    zone=self.current_zone,
                    location_tag=self.current_location_tag,
                    cycle=self.current_cycle,
                    wifi_measurement=wifi_measurement,
                    ping_measurement=ping_measurement
                )

                # Ajouter à la liste des records
                self.records.append(record)
                self.current_cycle += 1

                self.logger.debug(f"Nouvelle mesure enregistrée: {record}")

            except Exception as e:
                self.logger.error(f"Erreur lors du traitement des données WiFi: {str(e)}")

    def get_current_status(self) -> NetworkStatus:
        """Retourne le statut actuel basé sur la dernière mesure"""
        if not self.records:
            return NetworkStatus.UNKNOWN

        last_record = self.records[-1]
        wifi_meas = last_record.wifi_measurement
        ping_meas = last_record.ping_measurement

        # Vérifier les critères dans l'ordre du plus critique au moins critique

        signal_crit = self.wifi_thresholds['signal']['critical']
        loss_warn = self.wifi_thresholds['packet_loss']['warning']
        loss_crit = self.wifi_thresholds['packet_loss']['critical']
        latency_warn = self.wifi_thresholds['latency']['warning']
        latency_crit = self.wifi_thresholds['latency']['critical']

        if not wifi_meas or wifi_meas.signal_dbm <= signal_crit:

            return NetworkStatus.CRITICAL

        if not ping_meas:
            return NetworkStatus.WARNING


        if (ping_meas.lost_percent >= loss_crit or
            ping_meas.latency >= latency_crit):
            return NetworkStatus.CRITICAL

        if (ping_meas.lost_percent >= loss_warn or
            ping_meas.latency >= latency_warn):

            return NetworkStatus.WARNING

        return NetworkStatus.GOOD

    def get_latest_record(self) -> Optional[WifiRecord]:
        """Retourne le dernier enregistrement"""
        if not self.records:
            return None
        return self.records[-1]

    def collect_sample(self) -> Optional[WifiRecord]:
        """Collecte un échantillon complet de données WiFi"""
        start_time = time.time()
        self.logger.info("Démarrage de la collecte de données...")

        try:
            # Get latest record from PowerShell collector
            wifi_data = self.ps_collector.get_wifi_data()
            if not wifi_data:
                self.logger.error("Pas de données WiFi disponibles")
                return None

            # Create WiFi measurement
            wifi_measurement = self._create_wifi_measurement_from_ps(wifi_data)
            if not wifi_measurement:
                return None

            # Create ping measurement if we have a WiFi connection
            ping_measurement = None
            if wifi_measurement.ssid != "N/A":
                try:
                    # Try to ping default gateway
                    gateway_result = subprocess.run(
                        ["route", "print", "0.0.0.0"],
                        capture_output=True,
                        text=True
                    )

                    if gateway_result.returncode == 0:
                        gateway = gateway_result.stdout
                        gateway_match = re.search(r"0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)", gateway)
                        if gateway_match:
                            gateway_ip = gateway_match.group(1)
                            ping_result = subprocess.run(
                                ["ping", "-n", "1", gateway_ip],
                                capture_output=True,
                                text=True
                            )

                            ping_output = ping_result.stdout
                            time_match = re.search(r"temps[<=](\d+)ms", ping_output)
                            if time_match:
                                latency = int(time_match.group(1))
                                ping_measurement = PingMeasurement(
                                    latency=latency,
                                    packet_loss=0 if latency > 0 else 100
                                )
                except Exception as e:
                    self.logger.warning(f"Erreur lors du ping: {str(e)}")

            # Create record
            record = WifiRecord(
                timestamp=datetime.now(),
                zone=self.current_zone,
                location_tag=self.current_location_tag,
                cycle=self.current_cycle,
                wifi_measurement=wifi_measurement,
                ping_measurement=ping_measurement
            )

            # Save record
            with self.measurement_lock:
                self.records.append(record)
                self.current_cycle += 1

            collection_time = time.time() - start_time
            self.logger.info(f"Collecte terminée en {collection_time:.2f}s")

            # Log summary
            if wifi_measurement:
                self.logger.info(f"Connecté à {wifi_measurement.ssid} ({wifi_measurement.signal_dbm} dBm)")
            if ping_measurement:
                self.logger.info(f"Latence: {ping_measurement.latency}ms")

            return record

        except Exception as e:
            self.logger.error(f"Erreur lors de la collecte: {str(e)}", exc_info=True)
            return None

    def export_records(self, filename: Optional[str] = None) -> str:
        """Exporte les enregistrements dans un fichier JSON"""
        if not filename:
            filename = f"wifi_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = os.path.join(self.base_path, filename)
        records_data = [
            {
                "timestamp": record.timestamp.isoformat(),
                "zone": record.zone,
                "location_tag": record.location_tag,
                "cycle": record.cycle,
                "wifi": record.wifi_measurement.__dict__ if record.wifi_measurement else None,
                "ping": record.ping_measurement.__dict__ if record.ping_measurement else None
            }
            for record in self.records
        ]

        with open(filepath, 'w') as f:
            json.dump(records_data, f, indent=2)

        self.logger.info(f"Enregistrements exportés vers {filepath}")
        return filepath
