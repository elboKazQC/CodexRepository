import json
from unittest.mock import patch

from ui.moxa_view import MoxaView


def test_copy_json_to_clipboard(mock_tk_root, tmp_path):
    view = MoxaView(mock_tk_root, str(tmp_path), {"p": 1})
    view.copy_json()
    mock_tk_root.clipboard_clear.assert_called_once()
    mock_tk_root.clipboard_append.assert_called_once()
    expected = json.dumps({"p": 1}, indent=2)
    assert mock_tk_root.clipboard_append.call_args.args[0] == expected


def test_export_json(tmp_path, mock_tk_root):
    view = MoxaView(mock_tk_root, str(tmp_path), {"p": 2})
    export_file = tmp_path / "conf.json"
    with patch("tkinter.filedialog.asksaveasfilename", return_value=str(export_file)):
        view.export_json()
    assert json.loads(export_file.read_text()) == {"p": 2}
