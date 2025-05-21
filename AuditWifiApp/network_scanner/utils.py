"""Utility functions for WiFi scanning."""



def percentage_to_dbm(percentage: int) -> int:
    """Convert a signal percentage to dBm approximation."""
    if percentage >= 100:
        return -30
    if percentage >= 80:
        return -50
    if percentage >= 60:
        return -60
    if percentage >= 40:
        return -67
    if percentage >= 20:
        return -75
    return -85


def calculate_channel_from_frequency(frequency: int) -> int:
    """Return WiFi channel number from frequency in MHz."""
    if 2412 <= frequency <= 2484:
        if frequency == 2484:
            return 14
        if frequency == 2407:
            return 0
        if 2412 <= frequency <= 2472:
            return (frequency - 2412) // 5 + 1
        return int((frequency - 2407) / 5)
    if 5170 <= frequency <= 5825:
        if 5170 <= frequency <= 5240:
            return (frequency - 5170) // 5 + 34
        if 5250 <= frequency <= 5330:
            return (frequency - 5250) // 5 + 52
        if 5490 <= frequency <= 5710:
            return (frequency - 5490) // 5 + 100
        if 5735 <= frequency <= 5835:
            return (frequency - 5735) // 5 + 149
        return ((frequency - 5000) // 5) // 5 * 4 + 32
    if 5945 <= frequency <= 7125:
        return (frequency - 5950) // 5 + 1
    return 0


def frequency_to_band(frequency: int) -> str:
    """Return band name from frequency in MHz."""
    if 2400 <= frequency <= 2500:
        return "2.4 GHz"
    if 5100 <= frequency <= 5900:
        return "5 GHz"
    if 5945 <= frequency <= 7125:
        return "6 GHz"
    return "Inconnu"
