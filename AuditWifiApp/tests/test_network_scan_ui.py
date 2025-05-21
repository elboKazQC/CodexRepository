import csv
from unittest.mock import patch, MagicMock
import tkinter as tk

from ui.wifi_view import WifiView


class DummyAnalyzer:
    """Analyzer stub for WifiView tests."""

    def __init__(self) -> None:
        self.is_collecting = False
        self.wifi_collector = MagicMock()

    def start_analysis(self) -> bool:
        return True

    def stop_analysis(self) -> None:
        self.is_collecting = False

    def export_data(self, filepath: str) -> None:
        pass


def test_scan_wifi_populates_tree(mock_tk_root):
    mock_results = [
        {"ssid": "AP1", "signal": -40, "channel": 1, "frequency": "2.4 GHz"},
        {"ssid": "AP2", "signal": -50, "channel": 36, "frequency": "5 GHz"},
    ]
    with (
        patch("runner.scan_wifi", return_value=mock_results) as mock_scan,
        patch("ui.wifi_view.threading.Thread") as mock_thread,
    ):
        def make_thread(*args, **kwargs):
            target = kwargs.get("target")
            if target is None and args:
                target = args[0]
            class DummyThread:
                def __init__(self, target):
                    self.target = target
                def start(self):
                    self.target()
            return DummyThread(target)
        mock_thread.side_effect = make_thread
        ui = WifiView(mock_tk_root, DummyAnalyzer())
        ui.scan_nearby_aps()
        mock_scan.assert_called_once()
        items = ui.scan_tree.get_children()
        assert len(items) == 2
        first = ui.scan_tree.item(items[0])["values"]
        assert first[0] == "AP1"
        assert ui.export_scan_button["state"] == tk.NORMAL


def test_export_scan_results(tmp_path, mock_tk_root):
    mock_results = [
        {"ssid": "AP1", "signal": -40, "channel": 1, "frequency": "2.4 GHz"}
    ]
    with (
        patch("runner.scan_wifi", return_value=mock_results),
        patch("ui.wifi_view.threading.Thread") as mock_thread,
    ):
        def make_thread(*args, **kwargs):
            target = kwargs.get("target")
            if target is None and args:
                target = args[0]
            class DummyThread:
                def __init__(self, target):
                    self.target = target
                def start(self):
                    self.target()
            return DummyThread(target)
        mock_thread.side_effect = make_thread
        ui = WifiView(mock_tk_root, DummyAnalyzer())
        ui.scan_nearby_aps()
    export_file = tmp_path / "scan.csv"
    with patch("tkinter.filedialog.asksaveasfilename", return_value=str(export_file)):
        ui.export_scan_results()
    assert export_file.exists()
    with open(export_file, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["SSID", "Signal(dBm)", "Canal", "Bande"]
    assert rows[1][0] == "AP1"


def test_start_collection_triggers_scan(mock_tk_root):
    with (
        patch("runner.scan_wifi") as mock_scan,
        patch.object(WifiView, "update_data"),
        patch.object(WifiView, "update_status"),
        patch("ui.wifi_view.threading.Thread") as mock_thread,
    ):
        def make_thread(*args, **kwargs):
            target = kwargs.get("target")
            if target is None and args:
                target = args[0]
            class DummyThread:
                def __init__(self, target):
                    self.target = target
                def start(self):
                    self.target()
            return DummyThread(target)
        mock_thread.side_effect = make_thread
        ui = WifiView(mock_tk_root, DummyAnalyzer())
        with patch.object(ui.analyzer, "start_analysis", return_value=True):
            ui.start_collection()
        mock_scan.assert_called_once()


def test_filter_and_sorting(mock_tk_root):
    """Filtering by SSID and sorting by column should refresh the tree."""
    mock_results = [
        {"ssid": "AP1", "signal": -50, "channel": 1, "frequency": "2.4 GHz"},
        {"ssid": "AP2", "signal": -40, "channel": 6, "frequency": "2.4 GHz"},
        {"ssid": "Guest", "signal": -60, "channel": 11, "frequency": "2.4 GHz"},
    ]
    with (
        patch("runner.scan_wifi", return_value=mock_results),
        patch("ui.wifi_view.threading.Thread") as mock_thread,
    ):
        def make_thread(*args, **kwargs):
            target = kwargs.get("target")
            if target is None and args:
                target = args[0]
            class DummyThread:
                def __init__(self, target):
                    self.target = target
                def start(self):
                    self.target()
            return DummyThread(target)
        mock_thread.side_effect = make_thread
        ui = WifiView(mock_tk_root, DummyAnalyzer())
        ui.scan_nearby_aps()

    ui._on_heading_click("signal")
    items = ui.scan_tree.get_children()
    assert ui.scan_tree.item(items[0])["values"][0] == "Guest"

    ui._on_heading_click("signal")
    items = ui.scan_tree.get_children()
    assert ui.scan_tree.item(items[0])["values"][0] == "AP2"

    ui.scan_filter_var.set("AP")
    items = ui.scan_tree.get_children()
    assert len(items) == 2
    assert ui.scan_tree.item(items[0])["values"][0] == "AP2"


def test_scan_runs_in_background(mock_tk_root):
    """Scanning should not block the UI thread."""
    mock_result = [{"ssid": "AP1", "signal": -40, "channel": 1, "frequency": "2.4 GHz"}]

    def delayed_scan():
        import time
        time.sleep(0.1)
        return mock_result

    with patch("runner.scan_wifi", side_effect=delayed_scan):
        ui = WifiView(mock_tk_root, DummyAnalyzer())
        start = __import__("time").perf_counter()
        ui.scan_nearby_aps()
        elapsed = __import__("time").perf_counter() - start
        assert elapsed < 0.05
        ui._scan_thread.join()
        items = ui.scan_tree.get_children()
        assert len(items) == 1
