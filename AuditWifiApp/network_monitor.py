"""Module de surveillance réseau pour l'onglet Monitoring AMR.

Ce module fournit une fonction pour exécuter un ping sous Windows,
analyse la sortie et retourne un dictionnaire contenant la latence
moyenne, le taux de perte et un indicateur de qualité.

Bonus : possibilité d'enregistrer les résultats dans un fichier CSV.
"""

from __future__ import annotations

import csv
import os
import re
import subprocess
import time
from datetime import datetime
from typing import Dict, Optional


PING_COUNT = "4"
DEFAULT_IP = "192.168.1.1"


def _parse_ping_output(output: str) -> tuple[str, str, float]:
    """Extrait la perte et la latence moyenne depuis la sortie de ping."""
    loss_match = re.search(r"(\d+)%\s*loss", output, re.IGNORECASE)
    if not loss_match:
        loss_match = re.search(r"(\d+)%\s*perte", output, re.IGNORECASE)
    loss = loss_match.group(1) + "%" if loss_match else "100%"

    avg_match = re.search(r"Average\s*=\s*([0-9]+ms)", output, re.IGNORECASE)
    if not avg_match:
        avg_match = re.search(r"Moyenne\s*=\s*([0-9]+ms)", output, re.IGNORECASE)
    latency = avg_match.group(1) if avg_match else "0 ms"

    loss_value = float(loss_match.group(1)) if loss_match else 100.0
    return latency, loss, loss_value


def _quality_emoji(loss_value: float) -> str:
    """Retourne l'emoji correspondant à la qualité réseau."""
    if loss_value < 2:
        return "\U0001F535"  # 🔵
    if loss_value <= 5:
        return "\U0001F7E0"  # 🟠
    return "\U0001F534"  # 🔴


def ping_ip(ip: str = DEFAULT_IP, csv_path: Optional[str] = None) -> Dict[str, str]:
    """Réalise un ping et retourne les statistiques utiles.

    Args:
        ip: Adresse IP à tester.
        csv_path: Chemin d'un fichier CSV pour enregistrer le résultat.
    """
    try:
        output = subprocess.check_output(
            ["ping", "-n", PING_COUNT, ip],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding="utf-8",
        )
    except Exception:
        # En cas d'échec, on considère 100% de perte
        latency = "0 ms"
        loss = "100%"
        loss_value = 100.0
    else:
        latency, loss, loss_value = _parse_ping_output(output)

    quality = _quality_emoji(loss_value)
    result = {"ip": ip, "latence": latency, "perte": loss, "qualite": quality}

    if csv_path:
        _append_to_csv(csv_path, result)

    return result


def _append_to_csv(path: str, data: Dict[str, str]) -> None:
    """Ajoute un enregistrement dans un fichier CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=["timestamp", "ip", "latence", "perte", "qualite"]
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow({"timestamp": datetime.now().isoformat(), **data})


def monitor(ip: str = DEFAULT_IP, interval: float = 30.0, csv_path: Optional[str] = None) -> None:
    """Boucle de surveillance appelant ``ping_ip`` périodiquement."""
    try:
        while True:
            ping_ip(ip, csv_path)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
