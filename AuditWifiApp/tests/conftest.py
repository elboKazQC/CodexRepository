"""
Configuration and fixtures for pytest.
"""
import pytest
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
    patch_target = 'tkinter.Tk'
    with patch(patch_target) as mock_root, \
         patch('tkinter._get_default_root', return_value=mock_root.return_value):
        root = mock_root.return_value
        root.tk = MagicMock()
        root.tk.call = MagicMock(return_value=None)
        root.__str__ = lambda self=root: "mock"
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
    class DummyTreeview:
        def __init__(self, *args, **kwargs):
            self._items = []
            self.headings = {}

        def heading(self, col, text=None, command=None):
            self.headings[col] = text

        def column(self, col, width=None):
            pass

        def pack(self, *args, **kwargs):
            pass

        def insert(self, parent, index, values=()):
            self._items.append(values)
            return str(len(self._items))

        def delete(self, item):
            self._items = []

        def get_children(self):
            return [str(i + 1) for i in range(len(self._items))]

        def item(self, iid):
            return {"values": self._items[int(iid) - 1]}

        def yview(self, *args, **kwargs):
            return (0, 1)

        def configure(self, **kwargs):
            pass

        def grid(self, *args, **kwargs):
            pass

    class DummyButton:
        def __init__(self, *args, **kwargs):
            self.options = {"state": kwargs.get("state")}

        def pack(self, *args, **kwargs):
            pass

        def grid(self, *args, **kwargs):
            pass

        def config(self, **kwargs):
            self.options.update(kwargs)

        configure = config

        def __getitem__(self, key):
            return self.options.get(key)


    class DummyStringVar:
        def __init__(self, *args, **kwargs):
            self._value = ""
            self._callbacks = []

        def get(self) -> str:
            return self._value

        def set(self, value: str) -> None:
            self._value = value
            for cb in self._callbacks:
                cb()

        def trace_add(self, mode: str, callback):
            self._callbacks.append(callback)


    patches = [
        patch('tkinter.ttk.Style'),
        patch('tkinter.messagebox'),
        patch('log_manager.messagebox'),

        patch('tkinter.Text'),

        patch('tkinter.StringVar', DummyStringVar),

        patch('tkinter.ttk.Treeview', DummyTreeview),
        patch('tkinter.ttk.Button', DummyButton),
        patch('tkinter.ttk.OptionMenu'),
        patch('tkinter.Menu'),
        patch('matplotlib.backends.backend_tkagg.FigureCanvasTkAgg'),
        patch('runner.NetworkAnalyzerUI.setup_graphs', lambda self: None),
    ]
    try:
        __import__('ttkbootstrap')
        patches.append(patch('ttkbootstrap.style.Style'))
        patches.append(patch('ttkbootstrap.Window'))
        patches.append(patch('ttkbootstrap.OptionMenu'))
        patches.append(patch('ttkbootstrap.style.Bootstyle.update_ttk_widget_style'))
        patches.append(patch('ttkbootstrap.style.Bootstyle.update_tk_widget_style'))
    except Exception:
        pass

    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        yield
