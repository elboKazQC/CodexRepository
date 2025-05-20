"""
Tests for WiFi data collection and analysis functionality.
"""
import os
import pytest
from unittest.mock import MagicMock, patch
from src.ai.simple_wifi_analyzer import analyze_wifi_data
from wifi_test_manager import WifiTestManager

def test_wifi_data_analysis(sample_wifi_data, mock_openai_response):
    """Test WiFi data analysis functionality"""
    with patch('src.ai.simple_wifi_analyzer.requests.post') as mock_post:
        # Setup mock response
        mock_post.return_value.json.return_value = mock_openai_response
        mock_post.return_value.status_code = 200
        os.environ['OPENAI_API_KEY'] = 'test'
        
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
    mock_wifi_collector.get_latest_record.return_value = mock_wifi_collector.collect_sample.return_value
    
    # Crée le gestionnaire de test
    test_manager = WifiTestManager(mock_wifi_collector)
    
    # Simule le clic sur "Démarrer le test"
    with patch('wifi_test_manager.threading.Thread'):
        test_manager.start_wifi_test()
    assert test_manager.test_running
    test_manager.collected_data.append(mock_wifi_collector.collect_sample.return_value)
    assert len(test_manager.collected_data) > 0  # Vérifie que des données sont collectées
    
    # Simule le clic sur "Arrêter le test"
    test_manager.stop_wifi_test()
    assert not test_manager.test_running
    
    # Vérifie que les données sont prêtes pour l'analyse
    assert isinstance(test_manager.collected_data, list)
    wifi_sample = test_manager.collected_data[0]
    assert wifi_sample["rssi"] <= 0  # Un RSSI valide est toujours négatif
    assert 1 <= wifi_sample["channel"] <= 165  # Canaux WiFi valides

@pytest.mark.integration
def test_wifi_collection_integration(mock_tk_root, mock_wifi_collector):
    """Test integration of WiFi data collection with UI"""
    with patch('tkinter.StringVar') as mock_string_var, \
         patch('tkinter.BooleanVar') as mock_bool_var, \
         patch('tkinter.Text') as mock_text, \
         patch('tkinter.ttk.Frame'), \
         patch('tkinter.ttk.Button'), \
         patch('tkinter.ttk.Label'), \
         patch('tkinter.ttk.Style'), \
         patch('runner.FigureCanvasTkAgg'), \
         patch('wifi_test_manager.WifiTestManager') as mock_manager_class, \
         patch('wifi_data_collector.WifiDataCollector') as mock_collector_class:
        
        # Setup Text widget mock
        mock_text_instance = MagicMock()
        mock_text.return_value = mock_text_instance
        
        # Make sure our collector is used
        mock_collector_class.return_value = mock_wifi_collector
        
        # Setup WiFi manager mock
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        # Configure mocks
        mock_tk_root.StringVar = mock_string_var
        mock_tk_root.BooleanVar = mock_bool_var
        
        from runner import NetworkAnalyzerUI

        mock_analyzer = MagicMock()
        mock_analyzer.wifi_collector = mock_wifi_collector
        mock_analyzer.start_analysis.return_value = True
        mock_analyzer.is_collecting = True
        with patch('runner.NetworkAnalyzer', return_value=mock_analyzer):
            ui = NetworkAnalyzerUI(mock_tk_root)
            ui.start_collection()
            assert mock_analyzer.start_analysis.called
            ui.stop_collection()

def test_invalid_wifi_data():
    """Test handling of invalid WiFi data"""
    with patch('src.ai.simple_wifi_analyzer.requests.post') as mock_post:
        # Configure mock to return error
        mock_post.return_value.status_code = 400
        os.environ['OPENAI_API_KEY'] = 'test'
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
    
    # Collect data
    mock_wifi_collector.get_latest_record.return_value = mock_wifi_collector.collect_sample.return_value
    with patch('wifi_test_manager.threading.Thread'):
        test_manager.start_wifi_test()
    # Simuler la collecte d'un échantillon
    test_manager.collected_data.append(mock_wifi_collector.collect_sample.return_value)
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
