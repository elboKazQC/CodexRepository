"""
Tests qui simulent l'utilisation manuelle de l'application
"""
from unittest.mock import MagicMock, patch
from src.ai.simple_moxa_analyzer import analyze_moxa_logs
from wifi_test_manager import WifiTestManager
from wifi_data_collector import WifiDataCollector
import time

@patch('src.ai.simple_moxa_analyzer.create_retry_session')
def test_manual_moxa_workflow(mock_session):
    """Test simplified manual Moxa analysis workflow"""
    # Les logs qu'un utilisateur pourrait coller
    sample_logs = """
    2024-05-15 10:00:00 [INFO] Connection established with AP 00:11:22:33:44:55
    2024-05-15 10:00:01 [INFO] Signal strength: -65 dBm
    2024-05-15 10:00:02 [INFO] Channel: 6 (2.4 GHz)
    2024-05-15 10:01:00 [WARNING] Roaming initiated
    """
    
    session = MagicMock()
    session.post.return_value.status_code = 200
    session.post.return_value.json.return_value = {
        "choices": [{"message": {"content": "Analyse"}}]
    }
    mock_session.return_value = session

    result = analyze_moxa_logs(sample_logs, {"roaming_mechanism": "signal_strength"})

    assert "Analyse" in result

def test_manual_wifi_workflow():
    """Test qui simule exactement l'action de démarrer/arrêter un test WiFi"""
    # Mock le collecteur WiFi pour simuler des données réelles
    mock_collector = MagicMock(spec=WifiDataCollector)
    mock_collector.collect_sample.return_value = {
        "timestamp": "2024-05-15 10:00:00",
        "ssid": "Test_Network",
        "rssi": -65,
        "band": "2.4 GHz",
        "channel": 6,
        "noise": -95
    }
    
    test_manager = WifiTestManager(mock_collector)

    def fake_run(self):
        self.collected_data.append(mock_collector.collect_sample())
        self.test_running = False

    with patch.object(WifiTestManager, "_run_test", fake_run):
        test_manager.start_wifi_test()
        time.sleep(0.05)
        test_manager.stop_wifi_test()

        assert len(test_manager.collected_data) > 0
        sample = test_manager.collected_data[0]
        assert -100 <= sample["rssi"] <= 0  # RSSI valide
