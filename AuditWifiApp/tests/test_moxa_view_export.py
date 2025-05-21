import json
from unittest.mock import patch

from ui.moxa_view import MoxaView


def test_export_creates_json(tmp_path, mock_tk_root):
    """export_data should write analysis results to the selected file."""
    view = MoxaView(mock_tk_root, config_dir=str(tmp_path / "cfg"), default_config={})
    view.moxa_results.get.return_value = "some analysis"
    export_file = tmp_path / "res.json"
    with patch("tkinter.filedialog.asksaveasfilename", return_value=str(export_file)):
        view.export_data()
    assert export_file.exists()
    with open(export_file, encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["analysis"] == "some analysis"
