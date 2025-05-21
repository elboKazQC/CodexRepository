import os
import tkinter as tk
import importlib
from unittest.mock import patch

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


def test_edit_config_uses_checkbutton_for_bool(mock_tk_root, tmp_path):
    """Boolean fields should render as checkboxes in the edit dialog."""
    module = importlib.reload(moxa_view_module)
    view = module.MoxaView(mock_tk_root, str(tmp_path), {"enabled": True, "power": 5})

    with patch.object(module.ttk, "Checkbutton") as check_mock, \
         patch.object(module.tk, "Toplevel"):
        view.edit_config()

    # Only one boolean field should generate one Checkbutton
    assert check_mock.call_count == 1


def test_params_field_height_and_label(mock_tk_root, tmp_path):
    """The params text widget should be taller and label without example."""
    with patch("tkinter.Text") as text_mock, patch("tkinter.ttk.Label") as label_mock:
        module = importlib.reload(moxa_view_module)
        module.MoxaView(mock_tk_root, str(tmp_path), {})

    assert text_mock.call_args_list[3].kwargs.get("height") == 8
    texts = [c.kwargs.get("text") for c in label_mock.call_args_list]
    assert "Indiquez ici tout contexte supplémentaire" in texts
    assert all("roaming" not in t for t in texts if t)
