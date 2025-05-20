import pytest
from unittest.mock import patch, MagicMock

from wifi_data_collector import WifiDataCollector


class DummyMeasurement:
    """Simple stand-in for WifiMeasurement during tests."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_create_wifi_measurement_from_ps(tmp_path):
    """WifiDataCollector should convert PowerShell output into a measurement."""
    sample_data = {
        "SSID": "TestNet",
        "BSSID": "AA:BB:CC:DD:EE:FF",
        "SignalStrength": "80%",
        "SignalStrengthDBM": -60,
        "Channel": "6",
        "Band": "2.4 GHz",
        "ChannelUtilization": "25%",
    }

    with patch("wifi_data_collector.PowerShellWiFiCollector"):
        with patch("wifi_data_collector.WifiMeasurement", DummyMeasurement):
            collector = WifiDataCollector(base_path=str(tmp_path))
            measurement = collector._create_wifi_measurement_from_ps(sample_data)

    assert measurement.ssid == "TestNet"
    assert measurement.signal_dbm == -60
    assert measurement.frequency_mhz == 2437
