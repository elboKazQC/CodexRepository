from moxa_log_analyzer import MoxaLogAnalyzer
import log_manager  # Ensure module is loaded for patching in tests


def test_config_recommendations():
    logs = """2024-05-15 10:00:00 roaming started
2024-05-15 10:00:00 connected to ap [mac:11:22:33:44:55]
2024-05-15 10:00:01 roaming successful handoff time: 180 ms
2024-05-15 10:00:02 roaming snr: 8] [mac:11:22:33:44:55]
2024-05-15 10:00:03 connected to ap [mac:66:77:88:99:aa]
2024-05-15 10:00:04 roaming successful handoff time: 190 ms
2024-05-15 10:00:05 roaming snr: 7] [mac:66:77:88:99:aa]
2024-05-15 10:00:06 connected to ap [mac:11:22:33:44:55]
2024-05-15 10:00:07 roaming successful handoff time: 210 ms
2024-05-15 10:00:08 authentication failed
"""
    config = {
        "roaming_difference": 8,
        "max_transmission_power": 16,
        "rts_threshold": 2346,
        "fragmentation_threshold": 2346,
    }
    analyzer = MoxaLogAnalyzer()
    result = analyzer.analyze_logs(logs, config)
    changes = result.get("config_changes", [])
    names = {c["param"] for c in changes}
    assert "max_transmission_power" in names
    assert "rts_threshold" in names or "fragmentation_threshold" in names

