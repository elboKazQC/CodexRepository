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

from models.measurement_record import WifiMeasurement, PingMeasurement, NetworkStatus
from models.wifi_record import WifiRecord
from wifi.powershell_collector import PowerShellWiFiCollector

# Constantes de configuration
RETRY_CONFIG = {
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 2,  # secondes
    'SCAN_TIMEOUT': 10,  # secondes
    'PING_TIMEOUT': 10,  # secondes
}

# Seuils de qualité WiFi
WIFI_THRESHOLDS = {
    'SIGNAL_WEAK': -70,    # dBm, seuil pour signal faible
    'SIGNAL_CRITICAL': -80,  # dBm, seuil critique
    'PACKET_LOSS_WARNING': 10,  # %, seuil d'avertissement pour perte de paquets
    'PACKET_LOSS_CRITICAL': 20,  # %, seuil critique pour perte de paquets
    'LATENCY_WARNING': 100,  # ms, seuil d'avertissement pour la latence
    'LATENCY_CRITICAL': 200,  # ms, seuil critique pour la latence
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

    def __init__(self, base_path: str = "logs_moxa"):
        """Initialise le collecteur avec le chemin de base pour les logs"""
        self.base_path = base_path
        self.current_cycle: int = 0
        self.current_zone: str = "Non spécifiée"
        self.current_location_tag: str = ""
        self.is_collecting = False
        self.measurement_lock = threading.Lock()
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
            ssid = wifi_data.get('SSID', 'N/A')
            signal_percent = int(wifi_data.get('SignalStrength', '0').strip('%'))
            signal_dbm = wifi_data.get('SignalStrengthDBM')
            if signal_dbm is None and signal_percent > 0:
                # Convert percentage to dBm if not provided
                signal_dbm = -100 + (signal_percent * 0.5)
            else:
                signal_dbm = int(signal_dbm or -100)

            channel_val = int(wifi_data.get('Channel', '0'))
            band = wifi_data.get('Band', '2.4 GHz')  # Default to 2.4 GHz if not specified

            # Create measurement
            measurement = WifiMeasurement(
                ssid=ssid,
                bssid=wifi_data.get('BSSID', '00:00:00:00:00:00'),
                signal_percent=signal_percent,
                signal_dbm=signal_dbm,
                channel=channel_val,
                band=band,
                frequency=band,
                frequency_mhz=_channel_to_frequency_mhz(channel_val),
                is_connected=bool(ssid != 'N/A'),
                channel_utilization=float(wifi_data.get('ChannelUtilization', '0').strip('%')) / 100
            )

            self.logger.debug(f"Mesure WiFi créée: SSID={ssid}, "
                          f"Signal={signal_percent}% ({signal_dbm}dBm), "
                          f"Canal={channel_val}")

            return measurement

        except Exception as e:
            self.logger.error(f"Erreur lors de la création de la mesure WiFi: {str(e)}")
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
        if not wifi_meas or wifi_meas.signal_dbm <= WIFI_THRESHOLDS['SIGNAL_CRITICAL']:
            return NetworkStatus.CRITICAL

        if not ping_meas:
            return NetworkStatus.WARNING

        if (ping_meas.lost_percent >= WIFI_THRESHOLDS['PACKET_LOSS_CRITICAL'] or
            ping_meas.latency >= WIFI_THRESHOLDS['LATENCY_CRITICAL']):
            return NetworkStatus.CRITICAL

        if (ping_meas.lost_percent >= WIFI_THRESHOLDS['PACKET_LOSS_WARNING'] or
            ping_meas.latency >= WIFI_THRESHOLDS['LATENCY_WARNING']):
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
                    gateway = subprocess.check_output(["route", "print", "0.0.0.0"],
                                                   encoding='latin1',
                                                   stderr=subprocess.PIPE).decode('latin1')
                    gateway_match = re.search(r"0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)", gateway)
                    if gateway_match:
                        gateway_ip = gateway_match.group(1)
                        ping = subprocess.check_output(["ping", "-n", "1", gateway_ip],
                                                    encoding='latin1',
                                                    stderr=subprocess.PIPE).decode('latin1')
                        time_match = re.search(r"temps[<=](\d+)ms", ping)
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
