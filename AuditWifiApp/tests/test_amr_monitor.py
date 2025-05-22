import tkinter.messagebox  # ensure submodule exists for patching in fixtures
from unittest.mock import patch

from amr_ping_monitor import AmrPingMonitor
from ui import amr_view as amr_view_module


def test_monitor_add_remove_ip():
    monitor = AmrPingMonitor([])
    monitor.add_ip("192.168.0.10")
    assert "192.168.0.10" in monitor.ips
    monitor.remove_ip("192.168.0.10")
    assert "192.168.0.10" not in monitor.ips


def test_amr_view_add_and_remove(mock_tk_root):
    with patch.object(amr_view_module, "AmrPingMonitor") as MockMonitor:
        monitor_instance = MockMonitor.return_value
        view = amr_view_module.AmrMonitorView(mock_tk_root)
        view.ip_entry.get = lambda: "10.0.0.1"
        view.add_ip()
        item = view.ip_listbox.get_children()[0]
        assert view.ip_listbox.item(item)["values"][0] == "10.0.0.1"
        view.ip_listbox.selection = lambda: [item]
        view.remove_ip()
        assert not view.ip_listbox.get_children()

        view.ip_entry.get = lambda: "10.0.0.2"
        view.add_ip()
        view.start_monitoring()
        MockMonitor.assert_called_with(["10.0.0.2"], callback=view._on_status_change)
        monitor_instance.start.assert_called_once()
        view.stop_monitoring()
        monitor_instance.stop.assert_called_once()
