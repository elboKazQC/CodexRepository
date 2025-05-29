import subprocess
import threading
import time
import platform
import re
from typing import Callable, Dict, List, Optional

# Importer le module network_monitor pour utiliser ping_ip avec parsing des pertes
try:
    from network_monitor import ping_ip
    USE_NETWORK_MONITOR = True
except ImportError:
    USE_NETWORK_MONITOR = False

class AMRMonitor:
    """Monitor that continuously pings a list of AMR IP addresses with packet loss detection."""

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
                if USE_NETWORK_MONITOR:
                    # Utiliser network_monitor.ping_ip pour obtenir les pertes de paquets
                    ping_result = ping_ip(ip)
                    results[ip] = {
                        "reachable": ping_result.get('perte', '100%') != '100%',
                        "latency": self._extract_latency_ms(ping_result.get('latence', '0ms')),
                        "perte": ping_result.get('perte', '100%'),
                        "qualite": ping_result.get('qualite', '🔴')
                    }
                else:
                    # Fallback vers la méthode originale
                    reachable, latency = self._ping(ip)
                    results[ip] = {"reachable": reachable, "latency": latency}

            if self.callback:
                self.callback(results)
            time.sleep(self.interval)

    def _extract_latency_ms(self, latency_str: str) -> Optional[int]:
        """Extrait la valeur numérique de latence depuis une chaîne comme '15ms'"""
        try:
            # Chercher les chiffres dans la chaîne
            match = re.search(r'(\d+)', latency_str)
            return int(match.group(1)) if match else None
        except (ValueError, AttributeError):
            return None

    def _ping(self, ip: str) -> tuple[bool, Optional[int]]:
        """Méthode de ping de base (fallback)"""
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

