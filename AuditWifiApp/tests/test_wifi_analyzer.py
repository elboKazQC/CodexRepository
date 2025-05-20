"""
Tests for WiFi data collection and analysis functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
import time
from src.ai.simple_wifi_analyzer import analyze_wifi_data
from wifi_test_manager import WifiTestManager

def test_wifi_data_analysis(sample_wifi_data, mock_openai_response):
    """Test WiFi data analysis functionality"""
    with patch('src.ai.simple_wifi_analyzer.requests.post') as mock_post:
        # Setup mock response
        mock_post.return_value.json.return_value = mock_openai_response
        mock_post.return_value.status_code = 200
        
        # Run analysis
        result = analyze_wifi_data([sample_wifi_data])
        
        # Verify analysis result
        assert isinstance(result, str)
        assert len(result) > 0

def test_wifi_data_collection(mock_wifi_collector):
    """Test WiFi data collection process"""
    data = mock_wifi_collector.collect_sample()
    
    assert isinstance(data, dict)
    assert "signal_strength" in data
    assert "channel" in data

def test_wifi_test_manager(mock_wifi_collector):
    """Test WiFi test management functionality - simule le lancement d'un test WiFi et la collecte"""
    
    # Configure le mock pour simuler des données WiFi réelles
    mock_wifi_collector.collect_sample.return_value = {
        "timestamp": "2024-05-15 10:00:00",
        "ssid": "Test_Network",
        "rssi": -65,
        "band": "2.4 GHz",
        "channel": 6,
        "noise": -95
    }
    
    # Crée le gestionnaire de test
    test_manager = WifiTestManager(mock_wifi_collector)

    # Simule le clic sur "Démarrer le test" avec un run simplifié
    def fake_run(self):
        self.collected_data.append(mock_wifi_collector.collect_sample())
        self.test_running = False

    with patch.object(WifiTestManager, "_run_test", fake_run):
        test_manager.start_wifi_test()
        # Attendre que le thread termine
        time.sleep(0.05)
        assert len(test_manager.collected_data) > 0
    
    # Simule le clic sur "Arrêter le test"
    test_manager.stop_wifi_test()
    assert not test_manager.test_running
    
    # Vérifie que les données sont prêtes pour l'analyse
    assert isinstance(test_manager.collected_data, list)
    wifi_sample = test_manager.collected_data[0]
    assert wifi_sample["rssi"] <= 0  # Un RSSI valide est toujours négatif
    assert 1 <= wifi_sample["channel"] <= 165  # Canaux WiFi valides

@pytest.mark.integration
def test_wifi_collection_integration(mock_wifi_collector):
    """Integration test of WifiTestManager with simplified run."""
    manager = WifiTestManager(mock_wifi_collector)

    def fake_run(self):
        self.collected_data.append(mock_wifi_collector.collect_sample())
        self.test_running = False

    with patch.object(WifiTestManager, "_run_test", fake_run):
        manager.start_wifi_test()
        time.sleep(0.05)
        manager.stop_wifi_test()
        assert len(manager.collected_data) > 0

def test_invalid_wifi_data():
    """Test handling of invalid WiFi data"""
    with patch('src.ai.simple_wifi_analyzer.requests.post') as mock_post:
        # Configure mock to return error
        mock_post.return_value.status_code = 400
        with pytest.raises(Exception) as exc_info:
            analyze_wifi_data([{}])  # Empty data should raise error
        assert "Erreur API OpenAI" in str(exc_info.value)

def test_wifi_data_persistence(temp_log_file, mock_wifi_collector):
    """Test saving and loading of WiFi test data"""
    import json
    
    test_manager = WifiTestManager(mock_wifi_collector)

    # Configure mock collector
    mock_wifi_collector.collect_sample.return_value = {
        "timestamp": "2024-05-15 10:00:00",
        "ssid": "Test_Network",
        "rssi": -65,
        "band": "2.4 GHz",
        "channel": 6,
        "noise": -95
    }

    # Collect data with simplified run
    def fake_run(self):
        self.collected_data.append(mock_wifi_collector.collect_sample())
        self.test_running = False

    with patch.object(WifiTestManager, "_run_test", fake_run):
        test_manager.start_wifi_test()
        time.sleep(0.05)
        test_manager.stop_wifi_test()
    
    # Ensure data was collected
    assert hasattr(test_manager, "collected_data")
    assert len(test_manager.collected_data) > 0
    
    # Save data
    with open(temp_log_file, 'w') as f:
        json.dump(test_manager.collected_data, f)
    
    # Verify file exists
    assert temp_log_file.exists()
    
    # Load and verify data
    with open(temp_log_file, 'r') as f:
        loaded_data = json.load(f)
    
    assert loaded_data is not None
    assert isinstance(loaded_data, list)
    assert len(loaded_data) > 0
    assert loaded_data[0]["rssi"] == -65
    assert loaded_data[0]["channel"] == 6
