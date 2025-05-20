"""History management for generated reports.

This module implements the ``HistoryManager`` class used to keep track
of reports exported from the application. Reports are stored as JSON files
under ``logs/`` and indexed in a SQLite database. The API provides methods to
save new reports, list the stored ones and load a report by its identifier.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional


class HistoryManager:
    """Persist and retrieve generated reports."""

    def __init__(self, db_path: str | None = None, json_dir: str | None = None) -> None:
        self.json_dir = json_dir or os.path.join(os.path.dirname(__file__), "logs")
        self.db_path = db_path or os.path.join(self.json_dir, "reports.db")
        os.makedirs(self.json_dir, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create the SQLite table if it does not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    file_path TEXT NOT NULL
                )
                """
            )

    def save_report(self, report: Dict) -> str:
        """Save a report to JSON and register it in the database.

        Args:
            report: The report data to persist.

        Returns:
            Path to the JSON file created.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.json_dir, f"report_{timestamp}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO reports (timestamp, file_path) VALUES (?, ?)",
                (timestamp, filename),
            )
        return filename

    def list_reports(self) -> List[Dict[str, str]]:
        """Return the list of stored reports."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, timestamp, file_path FROM reports ORDER BY id DESC"
            ).fetchall()
        return [
            {"id": str(row[0]), "timestamp": row[1], "file": row[2]} for row in rows
        ]

    def load_report(self, report_id: int) -> Optional[Dict]:
        """Load a report by its identifier."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT file_path FROM reports WHERE id=?", (report_id,)
            ).fetchone()
        if not row:
            return None
        file_path = row[0]
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
