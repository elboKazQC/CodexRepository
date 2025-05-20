import csv
from unittest.mock import patch
import tkinter as tk

from runner import NetworkAnalyzerUI


def test_scan_wifi_populates_tree(mock_tk_root):
    mock_results = [
        {"ssid": "AP1", "signal": -40, "channel": 1, "frequency": "2.4 GHz"},
        {"ssid": "AP2", "signal": -50, "channel": 36, "frequency": "5 GHz"},
    ]
    with patch("runner.scan_wifi", return_value=mock_results) as mock_scan:
        ui = NetworkAnalyzerUI(mock_tk_root)
        ui.scan_nearby_aps()
        mock_scan.assert_called_once()
        items = ui.scan_tree.get_children()
        assert len(items) == 2
        first = ui.scan_tree.item(items[0])["values"]
        assert first[0] == "AP1"
        # export button should be enabled
        assert ui.export_scan_button["state"] == tk.NORMAL


def test_export_scan_results(tmp_path, mock_tk_root):
    mock_results = [
        {"ssid": "AP1", "signal": -40, "channel": 1, "frequency": "2.4 GHz"}
    ]
    with patch("runner.scan_wifi", return_value=mock_results):
        ui = NetworkAnalyzerUI(mock_tk_root)
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
    """start_collection should scan WiFi networks after starting."""
    with patch("runner.scan_wifi") as mock_scan, \
         patch.object(NetworkAnalyzerUI, "update_data"), \
         patch.object(NetworkAnalyzerUI, "update_status"):
        ui = NetworkAnalyzerUI(mock_tk_root)
        with patch.object(ui.analyzer, "start_analysis", return_value=True):
            ui.start_collection()
        mock_scan.assert_called_once()
