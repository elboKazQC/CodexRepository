import yaml
from unittest.mock import patch
from bootstrap_ui import BootstrapNetworkAnalyzerUI
import app_config


def test_bootstrap_ui_reads_theme_from_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("interface:\n  theme: flatly\n")
    with patch("bootstrap_ui.load_config", return_value=yaml.safe_load(cfg.read_text())), \
         patch("bootstrap_ui.save_config") as save_cfg, \
         patch("ttkbootstrap.Window") as win:
        win.return_value.style.theme_names.return_value = ["flatly", "darkly"]
        ui = BootstrapNetworkAnalyzerUI()
        win.assert_called_with(themename="flatly")
        assert ui._theme == "flatly"


def test_change_theme_updates_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("interface:\n  theme: darkly\n")
    store = yaml.safe_load(cfg.read_text())

    with patch("bootstrap_ui.load_config", return_value=store), \
         patch("bootstrap_ui.save_config") as save_cfg, \
         patch("ttkbootstrap.Window") as win:
        win.return_value.style.theme_names.return_value = ["darkly", "flatly"]
        ui = BootstrapNetworkAnalyzerUI()
        ui.change_theme("flatly")
        save_cfg.assert_called_once()
        assert save_cfg.call_args.args[0]["interface"]["theme"] == "flatly"


