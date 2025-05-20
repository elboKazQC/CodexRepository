from unittest.mock import MagicMock, patch

from wifi_test_manager import WifiTestManager


def test_start_and_stop_wifi_test():
    """WifiTestManager should start and stop collection via WifiDataCollector."""
    mock_collector = MagicMock()
    mock_collector.start_collection.return_value = True

    with patch.object(WifiTestManager, "_run_test", return_value=None):
        manager = WifiTestManager(mock_collector)
        manager.start_wifi_test()
        assert manager.test_running
        mock_collector.start_collection.assert_called_once()

        manager.stop_wifi_test()
        mock_collector.stop_collection.assert_called_once()
        assert not manager.test_running
