"""AMR ping monitoring utilities.

This module provides :class:`AmrPingMonitor` for monitoring
connectivity to multiple AMRs using the system ``ping`` command.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


@dataclass
class PingStatus:
    """Connection status information for an AMR."""

    reachable: bool
    last_change: float


class AmrPingMonitor:
    """Monitor multiple AMR IPs with periodic pings.

    IP addresses can be added or removed while monitoring is running.
    """

    def __init__(
        self,
        ips: List[str],
        interval: float = 1.0,
        callback: Optional[Callable[[str, bool], None]] = None,
    ) -> None:
        """Create a new monitor.

        Parameters
        ----------
        ips:
            List of IP addresses to monitor.
        interval:
            Delay between pings in seconds.
        callback:
            Optional function invoked when an IP status changes.
        """
        self.ips = list(ips)
        self.interval = interval
        self.callback = callback
        self.status: Dict[str, PingStatus] = {
            ip: PingStatus(False, time.time()) for ip in ips
        }
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # IP list management
    # ------------------------------------------------------------------
    def add_ip(self, ip: str) -> None:
        """Add an IP address to the monitoring list."""
        if ip not in self.ips:
            self.ips.append(ip)
            self.status[ip] = PingStatus(False, time.time())

    def remove_ip(self, ip: str) -> None:
        """Remove an IP address from the monitoring list."""
        if ip in self.ips:
            self.ips.remove(ip)
            self.status.pop(ip, None)

    def start(self) -> None:
        """Start monitoring in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop monitoring and wait for the thread to exit."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            for ip in list(self.ips):
                reachable = self._ping(ip)
                info = self.status[ip]
                if reachable != info.reachable:
                    info.reachable = reachable
                    info.last_change = time.time()
                    if self.callback:
                        self.callback(ip, reachable)
            time.sleep(self.interval)

    @staticmethod
    def _ping(ip: str) -> bool:
        """Send a single ping with a short timeout."""
        param = "-n" if sys.platform.startswith("win") else "-c"
        timeout_param = "-w" if sys.platform.startswith("win") else "-W"
        timeout = "1000" if sys.platform.startswith("win") else "1"
        cmd = ["ping", param, "1", timeout_param, timeout, ip]
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
