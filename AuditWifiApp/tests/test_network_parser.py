"""Tests for network_scanner.parser module."""

from unittest.mock import MagicMock, patch

from network_scanner.parser import get_channel_from_bssid


def fake_run(output: str):
    """Create a fake subprocess.run returning provided output."""
    def _run(*args, **kwargs):
        return MagicMock(returncode=0, stdout=output)

    return _run


def test_get_channel_from_bssid_parses_netsh():
    """get_channel_from_bssid should parse channel and frequency."""
    netsh_output = """
        SSID 1 : Test
            BSSID 1 : aa:bb:cc:dd:ee:ff
            Signal : 70%
            Radio type : 802.11ac
            Channel : 36
            Frequency : 5 GHz
    """
    with patch("network_scanner.parser.subprocess.run", side_effect=fake_run(netsh_output)):
        channel, band, freq = get_channel_from_bssid("aa:bb")
    assert channel == 36
    assert band == "5 GHz"
    assert freq == 5170
