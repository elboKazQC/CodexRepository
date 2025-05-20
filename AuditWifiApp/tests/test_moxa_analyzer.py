"""
Tests for Moxa log analysis functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.ai.simple_moxa_analyzer import analyze_moxa_logs
from log_manager import LogManager

def test_moxa_log_analysis(sample_moxa_logs):
    """Test basic Moxa log analysis functionality - simule le copier/coller de logs et le clic sur Analyser"""
    
    # Configuration simple pour le test
    test_config = {
        "min_transmission_rate": 6,
        "max_transmission_power": 20,
        "roaming_mechanism": "signal_strength"
    }

    # Mock la réponse OpenAI
    with patch('src.ai.simple_moxa_analyzer.requests.post') as mock_post:
        # Configure une réponse simple comme celle qu'on voit dans l'UI
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [{
                    "message": {
                        "content": "Analyse des logs Moxa :\n\n1. Problèmes détectés:\n- Signal faible détecté\n\n2. Recommandations:\n- Ajuster la puissance"
                    }
                }]
            }
        )
        
        # Simule le clic sur Analyser
        result = analyze_moxa_logs(sample_moxa_logs, test_config)
        
        # Vérifie qu'on obtient une analyse
        assert "Problèmes détectés" in result
        assert "Recommandations" in result

def test_empty_moxa_logs():
    """Test handling of empty Moxa logs"""
    with pytest.raises(ValueError) as exc_info:
        analyze_moxa_logs("", {})
    assert "logs vides" in str(exc_info.value).lower()

def test_log_manager_moxa_analysis(sample_moxa_logs):
    """Test Moxa log analysis through LogManager"""
    log_manager = LogManager()
    result = log_manager.analyze_logs(
        sample_moxa_logs, 
        {"roaming_mechanism": "signal_strength"},
        is_moxa_log=True
    )
    assert result is not None

@pytest.mark.integration
def test_moxa_ui_integration(mock_tk_root):
    """Test integration with UI for Moxa log analysis"""
    with patch('tkinter.StringVar') as mock_string_var, \
         patch('tkinter.BooleanVar') as mock_bool_var, \
         patch('tkinter.Text') as mock_text, \
         patch('tkinter.ttk.Frame'), \
         patch('tkinter.ttk.Button'), \
         patch('tkinter.ttk.Label'), \
         patch('src.ai.simple_moxa_analyzer.analyze_moxa_logs') as mock_analyze:
        
        # Setup Text widget mock
        mock_text_instance = MagicMock()
        mock_text_instance.get.return_value = "Sample log content"
        mock_text.return_value = mock_text_instance

        # Mock analyze_moxa_logs to return a response
        mock_analyze.return_value = "Mocked analysis results"

        # Configure root mocks
        mock_tk_root.StringVar = mock_string_var
        mock_tk_root.BooleanVar = mock_bool_var
        
        from runner import MoxaAnalyzerUI
        
        # Create UI instance with mocked components
        ui = MoxaAnalyzerUI(mock_tk_root)
        
        # Replace UI components with mocks
        ui.logs_input_text = mock_text_instance
        ui.results_text = mock_text_instance
        
        # Call analyze_logs method
        ui._analyze_logs()
