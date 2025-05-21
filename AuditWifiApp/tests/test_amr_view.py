from unittest.mock import patch

from ui.amr_view import AmrMonitorView


class DummyCanvas:
    def __init__(self, *a, **kw):
        self.calls = []

    def create_oval(self, *a, **kw):
        return 1

    def pack(self, *a, **kw):
        pass

    def itemconfigure(self, *a, **kw):
        self.calls.append((a, kw))


def test_add_remove_ip(mock_tk_root):
    with patch('tkinter.Canvas', DummyCanvas):
        view = AmrMonitorView(mock_tk_root)
        view.ip_entry_var.set('10.0.0.1')
        view.add_ip()
        assert '10.0.0.1' in view.rows
        view.remove_ip('10.0.0.1')
        assert '10.0.0.1' not in view.rows


def test_start_stop_monitoring(mock_tk_root):
    with patch('tkinter.Canvas', DummyCanvas), \
         patch('ui.amr_view.AmrPingMonitor') as Monitor:
        view = AmrMonitorView(mock_tk_root)
        view.ip_entry_var.set('10.0.0.2')
        view.add_ip()
        view.start_monitoring()
        Monitor.assert_called_once()
        Monitor.return_value.start.assert_called_once()
        view.stop_monitoring()
        Monitor.return_value.stop.assert_called_once()


def test_update_row_status_changes_color(mock_tk_root):
    with patch('tkinter.Canvas', DummyCanvas):
        view = AmrMonitorView(mock_tk_root)
        view.ip_entry_var.set('10.0.0.3')
        view.add_ip()
        _frame, canvas = view.rows['10.0.0.3']
        view._update_row_status('10.0.0.3', True)
        assert canvas.calls[-1][1]['fill'] == 'green'
        view._update_row_status('10.0.0.3', False)
        assert canvas.calls[-1][1]['fill'] == 'red'
