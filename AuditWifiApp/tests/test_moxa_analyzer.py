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
    session = MagicMock()
    session.post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "choices": [{
                "message": {
                    "content": "Analyse des logs Moxa :\n\n1. Problèmes détectés:\n- Signal faible détecté\n\n2. Recommandations:\n- Ajuster la puissance"
                }
            }]
        }
    )

    with patch('src.ai.simple_moxa_analyzer.create_retry_session', return_value=session):
        # Simule le clic sur Analyser
        result = analyze_moxa_logs(sample_moxa_logs, test_config)
        
        # Vérifie qu'on obtient une analyse
        assert "Problèmes détectés" in result
        assert "Recommandations" in result

def test_empty_moxa_logs():
    """Test handling of empty Moxa logs"""
    with pytest.raises(ValueError) as exc_info:
        analyze_moxa_logs("", {})
    assert "logs sont vides" in str(exc_info.value).lower()

def test_log_manager_moxa_analysis(sample_moxa_logs):
    """Test Moxa log analysis through LogManager"""
    log_manager = LogManager()
    session = MagicMock()
    session.post.return_value.status_code = 200
    session.post.return_value.json.return_value = {
        "choices": [{"message": {"content": "Analyse"}}]
    }
    with patch('src.ai.simple_moxa_analyzer.create_retry_session', return_value=session):
        result = log_manager.analyze_logs(
            sample_moxa_logs,
            {"roaming_mechanism": "signal_strength"},
            is_moxa_log=True
        )
    assert result is not None

@pytest.mark.integration
def test_moxa_ui_integration():
    """Simplified integration test using analyze_moxa_logs directly."""
    session = MagicMock()
    session.post.return_value.status_code = 200
    session.post.return_value.json.return_value = {
        "choices": [{"message": {"content": "Analyse"}}]
    }
    with patch('src.ai.simple_moxa_analyzer.create_retry_session', return_value=session):
        result = analyze_moxa_logs("log", {"roaming_mechanism": "signal"})
        assert "Analyse" in result
