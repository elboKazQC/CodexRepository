import os
import tkinter as tk
import importlib
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

from ui import moxa_view as moxa_view_module


def test_load_example_log_inserts_text(mock_tk_root, tmp_path):
    module = importlib.reload(moxa_view_module)
    view = module.MoxaView(mock_tk_root, str(tmp_path), {})
    view.load_example_log()
    view.moxa_input.delete.assert_called_once_with('1.0', tk.END)
    args = view.moxa_input.insert.call_args[0]
    assert 'Connection established' in args[1]


def test_show_metrics_help_displays_message(mock_tk_root, tmp_path):
    module = importlib.reload(moxa_view_module)
    view = module.MoxaView(mock_tk_root, str(tmp_path), {})
    view.show_metrics_help()
    module.messagebox.showinfo.assert_called_once()


def test_boolean_field_uses_checkbutton(mock_tk_root, tmp_path):
    """Boolean options should create a Checkbutton widget."""
    module = importlib.reload(moxa_view_module)
    with patch.object(module.ttk, "Checkbutton") as check_mock:
        module.MoxaView(mock_tk_root, str(tmp_path), {"enabled": True, "power": 5})

    # Only one boolean field should generate one Checkbutton
    assert check_mock.call_count == 1


def test_params_field_height_and_label(mock_tk_root, tmp_path):
    """The params text widget should be taller and label without example."""
    with patch("tkinter.Text") as text_mock, patch("tkinter.ttk.Label") as label_mock:
        module = importlib.reload(moxa_view_module)
        module.MoxaView(mock_tk_root, str(tmp_path), {})

    assert text_mock.call_args_list[2].kwargs.get("height") == 8
    texts = [c.kwargs.get("text") for c in label_mock.call_args_list]
    assert any(
        "Indiquez ici tout contexte supplémentaire" in t
        for t in texts if t
    )
    assert all("roaming" not in t for t in texts if t)


def test_error_dialog_on_analysis_failure(mock_tk_root, tmp_path):
    """An exception during analysis should display an error dialog."""
    module = importlib.reload(moxa_view_module)
    class DummyButton:
        def __init__(self):
            self.options = {}

        def config(self, **kwargs):
            self.options.update(kwargs)

        configure = config

        def __getitem__(self, key):
            return self.options.get(key)

    dummy = SimpleNamespace()
    dummy.moxa_input = MagicMock()
    dummy.moxa_input.get.return_value = "logs"
    dummy.moxa_params_text = MagicMock()
    dummy.moxa_params_text.get.return_value = ""
    dummy.moxa_results = MagicMock()
    dummy.analyze_button = DummyButton()
    dummy.export_button = DummyButton()
    dummy.config_manager = MagicMock(get_config=lambda: {})
    dummy.update_config_from_vars = lambda: None
    dummy.current_config = {}

    with patch.object(module, "analyze_moxa_logs", side_effect=Exception("oops")):
        module.MoxaView.analyze_moxa_logs(dummy)
        module.messagebox.showerror.assert_called_once()
        assert dummy.analyze_button.options["state"] == tk.NORMAL
