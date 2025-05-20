import json
from unittest.mock import patch, MagicMock

from wifi.powershell_collector import PowerShellWiFiCollector
from wifi.wifi_analyzer import WifiAnalyzer
from models.measurement_record import WifiMeasurement


def test_collector_parses_noise_and_snr():
    collector = PowerShellWiFiCollector()
    ps_output = json.dumps({
        "SSID": "TestNet",
        "SignalStrength": "70%",
        "SignalStrengthDBM": -65,
        "NoiseFloor": -90,
        "SNR": 25,
        "Channel": 6
    })
    fake_result = MagicMock(returncode=0, stdout=ps_output)
    with patch('subprocess.run', return_value=fake_result):
        data = collector.get_wifi_data()

    assert data["NoiseFloor"] == -90
    assert data["SNR"] == 25


def test_analyzer_evaluates_snr():
    analyzer = WifiAnalyzer()
    metrics = analyzer._analyze_metrics({"rssi": -60, "snr": 12, "ping": 10, "packet_loss": 0})
    assert metrics["snr_quality"] == "Moyen"


def test_wifi_measurement_stores_noise_and_snr():
    m = WifiMeasurement(
        ssid="t",
        bssid="00:11",
        signal_percent=50,
        signal_dbm=-70,
        channel=1,
        band="2.4 GHz",
        frequency="2.4 GHz",
        frequency_mhz=2412,
        is_connected=True,
        channel_utilization=0.1,
        noise_floor=-95,
        snr=25
    )
    assert m.noise_floor == -95
    assert m.snr == 25
