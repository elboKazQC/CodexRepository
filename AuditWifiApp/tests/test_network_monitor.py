from unittest.mock import patch

from network_monitor import ping_ip


SAMPLE_OK = """Pinging 192.168.1.1 with 32 bytes of data:
Reply from 192.168.1.1: bytes=32 time=10ms TTL=64
Reply from 192.168.1.1: bytes=32 time=10ms TTL=64

Ping statistics for 192.168.1.1:
    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 10ms, Maximum = 10ms, Average = 10ms
"""

SAMPLE_LOSS = """Pinging 192.168.1.1 with 32 bytes of data:
Request timed out.
Reply from 192.168.1.1: bytes=32 time=100ms TTL=64

Ping statistics for 192.168.1.1:
    Packets: Sent = 4, Received = 3, Lost = 1 (25% loss),
Approximate round trip times in milli-seconds:
    Minimum = 100ms, Maximum = 100ms, Average = 100ms
"""


def test_ping_success_parsing():
    with patch("network_monitor.subprocess.check_output", return_value=SAMPLE_OK):
        result = ping_ip("192.168.1.1")
    assert result["perte"] == "0%"
    assert result["latence"] == "10ms"
    assert result["qualite"] == "\U0001F535"


def test_ping_packet_loss_parsing():
    with patch(
        "network_monitor.subprocess.check_output",
        return_value=SAMPLE_LOSS,
    ):
        result = ping_ip("192.168.1.1")
    assert result["perte"] == "25%"
    assert result["latence"] == "100ms"
    assert result["qualite"] == "\U0001F534"
