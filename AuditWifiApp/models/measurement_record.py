"""
Modèles de données pour les mesures WiFi
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

class NetworkStatus(Enum):
    """États possibles du réseau"""
    UNKNOWN = "UNKNOWN"
    NO_SIGNAL = "NO_SIGNAL"
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    GOOD = "GOOD"

@dataclass
class WifiMeasurement:
    """Mesure WiFi à un instant donné"""
    bssid: str
    ssid: str
    signal_strength: int
    channel: int
    frequency: str
    band: str
    encryption: str
    network_type: str

@dataclass
class PingMeasurement:
    """Mesure de connectivité réseau"""
    latency: int  # en millisecondes
    jitter: float = 0.0  # variation de la latence
    packet_loss: int = 0  # pourcentage de perte de paquets

@dataclass
class MeasurementRecord:
    """Enregistrement complet d'une mesure, incluant WiFi et métadonnées"""
    timestamp: datetime
    wifi_measurement: WifiMeasurement
    ping_measurement: Optional[PingMeasurement] = None
    zone: str = "Non spécifiée"
    signal_dbm: int = 0
    signal_percent: int = 0
    channel: int = 0
    frequency: str = ""
    frequency_mhz: int = 0
    status: NetworkStatus = NetworkStatus.UNKNOWN
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialisation après création de l'instance"""
        if self.metadata is None:
            self.metadata = {}
