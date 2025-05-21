"""Tests for network_scanner.utils module."""

from network_scanner.utils import (
    calculate_channel_from_frequency,
    frequency_to_band,
    percentage_to_dbm,
)


def test_percentage_to_dbm_mapping():
    """percentage_to_dbm should map percent values to expected dBm."""
    assert percentage_to_dbm(100) == -30
    assert percentage_to_dbm(85) == -50
    assert percentage_to_dbm(65) == -60
    assert percentage_to_dbm(45) == -67
    assert percentage_to_dbm(25) == -75
    assert percentage_to_dbm(10) == -85


def test_calculate_channel_from_frequency():
    """Validate channel calculation from frequency."""
    assert calculate_channel_from_frequency(2412) == 1
    assert calculate_channel_from_frequency(2437) == 6
    assert calculate_channel_from_frequency(5180) == 36


def test_frequency_to_band():
    """Check frequency band detection."""
    assert frequency_to_band(2462) == "2.4 GHz"
    assert frequency_to_band(5500) == "5 GHz"
    assert frequency_to_band(6000) == "6 GHz"
    assert frequency_to_band(1000) == "Inconnu"
