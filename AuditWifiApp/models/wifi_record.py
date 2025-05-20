"""
Modèle pour un enregistrement WiFi complet
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .measurement_record import WifiMeasurement, PingMeasurement

@dataclass
class WifiRecord:
    """Un enregistrement WiFi complet avec mesures et metadata"""
    timestamp: datetime
    zone: str
    location_tag: str
    cycle: int
    wifi_measurement: WifiMeasurement
    ping_measurement: Optional[PingMeasurement] = None
