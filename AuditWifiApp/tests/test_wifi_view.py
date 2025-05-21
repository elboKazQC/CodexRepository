from unittest.mock import MagicMock, patch

from ui.wifi_view import WifiView
from wifi.wifi_collector import WifiSample


def make_sample(signal=-50, quality=80, tx="54 Mbps", rx="54 Mbps"):
    return WifiSample(
        timestamp="t",
        ssid="test",
        bssid="00:00",
        signal_strength=signal,
        quality=quality,
        channel=1,
        band="2.4",
        status="connected",
        transmit_rate=tx,
        receive_rate=rx,
        raw_data={"TransmitRate": tx, "ReceiveRate": rx},
        location_tag="",
    )


def test_update_stats_colours_labels(mock_tk_root):
    class DummyLabel:
        def __init__(self, *_, **kw):
            self.options = kw

        def pack(self, *a, **kw):
            pass

        def config(self, **kw):
            self.options.update(kw)

        configure = config

        def cget(self, key):
            return self.options.get(key)

        def __getitem__(self, key):
            return self.options.get(key)

    with patch('tkinter.ttk.Label', DummyLabel):
        analyzer = MagicMock()
        view = WifiView(mock_tk_root, analyzer)
        sample = make_sample()
        view.samples = [sample] * 20
        view.update_stats()

        assert "54 Mbps" in view.tx_label.cget("text")
        assert view.signal_label.cget("foreground") == "green"
        assert view.quality_label.cget("foreground") == "green"
