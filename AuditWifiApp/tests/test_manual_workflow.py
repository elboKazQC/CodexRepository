"""
Tests qui simulent l'utilisation manuelle de l'application
"""
from unittest.mock import MagicMock, patch
from runner import MoxaAnalyzerUI
from wifi_test_manager import WifiTestManager
from wifi_data_collector import WifiDataCollector

@patch('runner.analyze_moxa_logs')  # Patch où la fonction est utilisée
def test_manual_moxa_workflow(mock_analyze):
    """Test qui simule exactement l'action de coller des logs et cliquer sur Analyser"""
    # Les logs qu'un utilisateur pourrait coller
    sample_logs = """
    2024-05-15 10:00:00 [INFO] Connection established with AP 00:11:22:33:44:55
    2024-05-15 10:00:01 [INFO] Signal strength: -65 dBm
    2024-05-15 10:00:02 [INFO] Channel: 6 (2.4 GHz)
    2024-05-15 10:01:00 [WARNING] Roaming initiated
    """
    
    # Configure le mock pour retourner une analyse
    mock_analyze.return_value = "Analyse des logs :\n1. Problèmes détectés\n2. Recommandations"
    
    # Mock les composants Tkinter
    with patch('tkinter.Tk') as mock_tk, \
         patch('tkinter.Text') as mock_text, \
         patch('tkinter.StringVar') as mock_string_var, \
         patch('tkinter.BooleanVar') as mock_bool_var:
            
        # Configure les mocks Tkinter
        root = mock_tk()
        root.StringVar = mock_string_var
        root.BooleanVar = mock_bool_var
        
        # Crée l'UI
        ui = MoxaAnalyzerUI(root)
        
        # Configure les widgets de l'UI
        mock_text_instance = MagicMock()
        mock_text_instance.get = lambda *args: sample_logs
        ui.logs_input_text = mock_text_instance
        ui.results_text = mock_text_instance
        
        # Force la config pour que l'analyse fonctionne
        ui.config_manager.config = {
            "min_transmission_rate": 6,
            "max_transmission_power": 20,
            "rts_threshold": 512,
            "roaming_mechanism": "signal_strength"
        }
        
        # Simule le clic sur Analyser
        ui.analyze_logs_from_input(sample_logs)
        
        # Vérifie que l'analyse a été faite
        assert mock_analyze.called
        assert mock_analyze.call_args[0][0] == sample_logs  # Vérifie que les logs sont passés
        mock_text_instance.delete.assert_called()
        mock_text_instance.insert.assert_called()

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
    
    # Mock l'UI Tkinter
    with patch('tkinter.Tk') as mock_tk, \
         patch('tkinter.Text') as mock_text:
            
        root = mock_tk()
        test_manager = WifiTestManager(mock_collector)
        
        # 1. Simule le clic sur "Démarrer le test"
        test_manager.start_wifi_test()
        assert test_manager.test_running
        
        # Vérifie que des données sont collectées
        assert len(test_manager.collected_data) > 0
        
        # 2. Simule le clic sur "Arrêter le test"
        test_manager.stop_wifi_test()
        assert not test_manager.test_running
        
        # Vérifie que l'analyse peut être faite
        sample = test_manager.collected_data[0]
        assert -100 <= sample["rssi"] <= 0  # RSSI valide
