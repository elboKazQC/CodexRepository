"""
Configuration and fixtures for pytest.
"""
import pytest
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Charger les variables d'environnement de test
def pytest_configure(config):
    """Configure l'environnement de test."""
    load_dotenv('.env.test')

@pytest.fixture
def sample_moxa_logs():
    """Sample Moxa logs for testing"""
    return """2023-12-15 10:00:00 [INFO] Connection established with AP 00:11:22:33:44:55
2023-12-15 10:00:01 [INFO] Signal strength: -65 dBm
2023-12-15 10:00:02 [INFO] Channel: 6 (2.4 GHz)
2023-12-15 10:01:00 [WARNING] Roaming initiated"""

@pytest.fixture
def sample_wifi_data():
    """Sample WiFi data for testing"""
    return {
        "signal_strength": -65,
        "channel": 6,
        "band": "2.4 GHz",
        "ssid": "Test_Network",
        "rssi": -65,
        "noise": -95,
        "snr": 30
    }

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "choices": [{
            "message": {
                "content": "Test analysis results with analysis and recommendations",
                "role": "assistant"
            },
            "finish_reason": "stop",
            "index": 0
        }],
        "created": 1683923731,
        "id": "mock-response",
        "model": "gpt-4",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 50,
            "prompt_tokens": 100,
            "total_tokens": 150
        }
    }

@pytest.fixture
def mock_tk_root():
    """Mock Tkinter root window for UI tests"""
    with patch('tkinter.Tk') as mock_tk:
        root = mock_tk.return_value
        yield root

@pytest.fixture
def mock_wifi_collector():
    """Mock WiFi data collector"""
    collector = MagicMock()
    collector.collect_sample.return_value = {
        "signal_strength": -65,
        "channel": 6,
        "band": "2.4 GHz",
        "ssid": "Test_Network",
        "rssi": -65,
        "noise": -95,
        "snr": 30
    }
    return collector

@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file for testing"""
    log_file = tmp_path / "test_log.txt"
    log_file.write_text("Test log content")
    return log_file
