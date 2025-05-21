import pytest
from unittest.mock import patch, MagicMock

from network_scanner import scan_wifi


def fake_subprocess_run_factory(output_mapping):
    """Create a fake subprocess.run that returns pre-defined outputs."""

    def _fake_run(args, capture_output=True, text=True, check=False, encoding=None, timeout=None):
        command = " ".join(args)
        stdout = output_mapping.get(command, "")
        return MagicMock(returncode=0, stdout=stdout)

    return _fake_run


def test_scan_wifi_parses_netsh_output():
    """scan_wifi should parse netsh output and return list of networks."""
    netsh_output = """
Interface name : Wi-Fi
There are 2 networks currently visible.

SSID 1 : Network1
    BSSID 1                 : aa:bb:cc:dd:ee:ff
    Signal                  : 70%
    Radio type              : 802.11ac
    Channel                 : 36

SSID 2 : Network2
    BSSID 1                 : 11:22:33:44:55:66
    Signal                  : 40%
    Radio type              : 802.11n
    Channel                 : 6
"""

    output_mapping = {
        "netsh wlan show networks mode=bssid": netsh_output,
        "netsh wlan show interface": "",
        "netsh wlan show all": "",
    }

    with patch("network_scanner.subprocess.run", side_effect=fake_subprocess_run_factory(output_mapping)):
        networks = scan_wifi()

    assert isinstance(networks, list)
    assert len(networks) == 2
    for net in networks:
        assert isinstance(net, dict)
        assert set(["ssid", "signal", "channel", "frequency"]).issubset(net.keys())
