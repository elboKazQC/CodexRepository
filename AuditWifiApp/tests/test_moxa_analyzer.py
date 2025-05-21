"""
Tests for Moxa log analysis functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
import requests
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



def test_deauth_metrics(moxa_logs_with_deauth):
    """Verify that deauthentication events are counted"""
    from moxa_log_analyzer import MoxaLogAnalyzer

    analyzer = MoxaLogAnalyzer()
    result = analyzer.analyze_logs(moxa_logs_with_deauth, {})

    assert result["analyse_detaillee"]["deauth_requests"]["total"] == 1
    assert result["analyse_detaillee"]["deauth_requests"]["par_ap"]["aa:bb:cc:dd:ee:ff"] == 1


def test_moxa_api_connection_error(sample_moxa_logs):
    """Ensure a friendly message is raised when the API is unreachable."""
    session = MagicMock()
    session.post.side_effect = requests.exceptions.ConnectionError()
    with patch('src.ai.simple_moxa_analyzer.create_retry_session', return_value=session):
        with pytest.raises(Exception) as exc_info:
            analyze_moxa_logs(sample_moxa_logs, {})
        assert "Impossible de contacter le service OpenAI" in str(exc_info.value)


def test_additional_params_in_prompt(sample_moxa_logs):
    """Ensure additional parameters are injected in the prompt."""
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=60):
        captured["prompt"] = json["messages"][0]["content"]
        class R:
            status_code = 200
            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}
        return R()

    session = MagicMock()
    session.post.side_effect = fake_post
    with patch('src.ai.simple_moxa_analyzer.create_retry_session', return_value=session):
        analyze_moxa_logs(sample_moxa_logs, {}, "roaming=snr")

    assert "Param\u00e8tres suppl\u00e9mentaires" in captured["prompt"]
    assert "roaming=snr" in captured["prompt"]


def test_additional_params_too_long(sample_moxa_logs):
    """Ensure validation triggers when params exceed length."""
    long_params = "a" * 501
    with pytest.raises(ValueError) as exc_info:
        analyze_moxa_logs(sample_moxa_logs, {}, long_params)
    assert "trop longs" in str(exc_info.value)


def test_additional_params_sanitization(sample_moxa_logs):
    """Non-printable characters should be removed from the prompt."""
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=60):
        captured["prompt"] = json["messages"][0]["content"]

        class R:
            status_code = 200

            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}

        return R()

    session = MagicMock()
    session.post.side_effect = fake_post
    with patch('src.ai.simple_moxa_analyzer.create_retry_session', return_value=session):
        analyze_moxa_logs(sample_moxa_logs, {}, "abc\n\tdef")

    assert "abcdef" in captured["prompt"]
    assert "abc\n\tdef" not in captured["prompt"]

