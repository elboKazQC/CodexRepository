"""
Configuration and fixtures for pytest.
"""
import pytest  # type: ignore
from unittest.mock import MagicMock, patch
from contextlib import ExitStack
from dotenv import load_dotenv
import os

# Charger les variables d'environnement de test
def pytest_configure(config):
    """Configure l'environnement de test."""
    load_dotenv('.env.test')
    os.environ.setdefault('OPENAI_API_KEY', 'test-key')

@pytest.fixture
def sample_moxa_logs():
    """Sample Moxa logs for testing"""
    return """2023-12-15 10:00:00 [INFO] Connection established with AP 00:11:22:33:44:55
2023-12-15 10:00:01 [INFO] Signal strength: -65 dBm
2023-12-15 10:00:02 [INFO] Channel: 6 (2.4 GHz)
2023-12-15 10:01:00 [WARNING] Roaming initiated"""


@pytest.fixture
def moxa_logs_with_deauth(sample_moxa_logs):
    """Sample logs containing a deauthentication event"""
    return sample_moxa_logs + "\n2023-12-15 10:02:00 [WARNING] Deauthentication from AP [MAC: AA:BB:CC:DD:EE:FF]"

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
    """Mock root window for UI tests."""
    try:
        patch_target = 'ttkbootstrap.Window'
        __import__('ttkbootstrap')
    except Exception:
        patch_target = 'tkinter.Tk'
    with patch(patch_target) as mock_root:
        root = mock_root.return_value
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

@pytest.fixture(autouse=True)
def patch_ttk_style():
    """Patch style classes to avoid initializing real GUI elements."""
    patches = [
        patch('tkinter.ttk.Style'),
        patch('tkinter.messagebox.showinfo'),
        patch('tkinter.messagebox.showerror'),
        patch('tkinter.messagebox.showwarning'),
        patch('log_manager.messagebox'),
    ]
    try:
        __import__('ttkbootstrap')
        patches.append(patch('ttkbootstrap.Style'))
        patches.append(patch('ttkbootstrap.Window'))
    except Exception:
        pass
    with ExitStack() as stack:
        for p in patches:
            try:
                stack.enter_context(p)
            except AttributeError:
                # Ignorer les patches qui ne peuvent pas être appliqués
                pass
        yield
