import tkinter as tk
from unittest.mock import MagicMock

from ui.wifi_view import WifiView


class DummyAnalyzer:
    """Simple analyzer stub used for WifiView tests."""

    def __init__(self) -> None:
        self.is_collecting = False
        self.wifi_collector = MagicMock()

    def start_analysis(self) -> bool:
        return True

    def stop_analysis(self) -> None:
        self.is_collecting = False

    def export_data(self, filepath: str) -> None:
        pass


def test_wifi_view_exposes_alert_text(mock_tk_root):
    """WifiView should create an alert text widget for journal messages."""
    view = WifiView(mock_tk_root, DummyAnalyzer())
    assert hasattr(view, "wifi_alert_text")
