import subprocess
import threading
import time
import platform
import re
from typing import Callable, Dict, List, Optional

class AMRMonitor:
    """Monitor that continuously pings a list of AMR IP addresses."""

    def __init__(self, ips: Optional[List[str]] = None, interval: float = 5.0):
        self.ips = ips or []
        self.interval = interval
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.callback: Optional[Callable[[Dict[str, Dict[str, Optional[int]]]], None]] = None

    def start(self, callback: Callable[[Dict[str, Dict[str, Optional[int]]]], None]) -> None:
        """Start monitoring by pinging all IPs at the given interval."""
        if self._running:
            return
        self.callback = callback
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.1)

    def _run(self) -> None:
        while self._running:
            results = {}
            for ip in list(self.ips):
                reachable, latency = self._ping(ip)
                results[ip] = {"reachable": reachable, "latency": latency}
            if self.callback:
                self.callback(results)
            time.sleep(self.interval)

    def _ping(self, ip: str) -> tuple[bool, Optional[int]]:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        try:
            output = subprocess.check_output(
                ["ping", param, "1", ip],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=2,
            )
            match = re.search(r"time[=<](\d+)", output)
            latency = int(match.group(1)) if match else None
            return True, latency
        except Exception:
            return False, None

