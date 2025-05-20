import matplotlib.figure
import pytest
from datetime import datetime
import tkinter.messagebox  # Ensure submodule exists for patching in fixtures

from heatmap_generator import generate_heatmap
from models.measurement_record import WifiMeasurement
from models.wifi_record import WifiRecord


def _measurement(dbm=-60) -> WifiMeasurement:
    return WifiMeasurement(
        ssid="Test",
        bssid="00:11:22:33:44:55",
        signal_percent=50,
        signal_dbm=dbm,
        channel=1,
        band="2.4",
        frequency="2.4",
        frequency_mhz=2412,
        is_connected=True,
        channel_utilization=0.1,
    )


def test_heatmap_with_tag_map():
    rec1 = WifiRecord(datetime.now(), "zone", "A", 0, _measurement())
    rec2 = WifiRecord(datetime.now(), "zone", "B", 1, _measurement(-70))
    tag_map = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
    fig = generate_heatmap([rec1, rec2], tag_map=tag_map)
    assert isinstance(fig, matplotlib.figure.Figure)


def test_heatmap_without_tag_map_fails():
    rec = WifiRecord(datetime.now(), "zone", "A", 0, _measurement())
    with pytest.raises(ValueError):
        generate_heatmap([rec])
