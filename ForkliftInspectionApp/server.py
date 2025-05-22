"""Minimal web server for forklift inspections using only standard library."""
from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import Dict
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

import yaml

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

HTML_FORM = """
<!DOCTYPE html>
<html lang='en'>
<head><meta charset='UTF-8'><title>Forklift Inspection</title></head>
<body>
<h1>Forklift Inspection Form</h1>
<form method='post'>
<label>Operator:<br><input type='text' name='operator' required></label><br>
<label>Forklift ID:<br><input type='text' name='forklift_id' required></label><br>
<label>Battery Level (%):<br><input type='number' name='battery_level' min='0' max='100' required></label><br>
<label><input type='checkbox' name='tires_ok'> Tires OK</label><br>
<label>Notes:<br><textarea name='notes' rows='4' cols='40'></textarea></label><br>
<button type='submit'>Submit</button>
</form>
</body>
</html>
"""

SUCCESS_PAGE = """<html><body><h1>Inspection Saved</h1><p>Report saved.</p><a href='/'>New inspection</a></body></html>"""


def load_config(path: str | None = None) -> Dict[str, str]:
    """Load YAML configuration.

    Parameters
    ----------
    path: str | None
        Optional path to the YAML configuration file. If ``None``,
        :data:`DEFAULT_CONFIG_PATH` is used.
    """
    if path is None:
        path = DEFAULT_CONFIG_PATH
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def save_inspection(data: Dict[str, str], config: Dict[str, str]) -> str:
    """Append inspection data to the configured CSV file."""
    dest_dir = config.get("storage_dir", "inspections")
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, config.get("file_name", "forklift_inspections.csv"))
    file_exists = os.path.exists(dest_file)
    with open(dest_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(data.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
    return dest_file


def app(environ, start_response):
    """WSGI application returning the form and handling submissions."""
    config = load_config()
    if environ["REQUEST_METHOD"] == "POST":
        length = int(environ.get("CONTENT_LENGTH", 0) or 0)
        body = environ["wsgi.input"].read(length).decode()
        fields = parse_qs(body)
        form_data = {
            "date": datetime.now().isoformat(timespec="seconds"),
            "operator": fields.get("operator", [""])[0],
            "forklift_id": fields.get("forklift_id", [""])[0],
            "battery_level": fields.get("battery_level", [""])[0],
            "tires_ok": "yes" if "tires_ok" in fields else "no",
            "notes": fields.get("notes", [""])[0],
        }
        save_inspection(form_data, config)
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [SUCCESS_PAGE.encode("utf-8")]

    start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
    return [HTML_FORM.encode("utf-8")]


def run(host: str = "0.0.0.0", port: int = 8000):  # pragma: no cover - manual run
    """Run the web server."""
    with make_server(host, port, app) as server:
        print(f"Serving on http://{host}:{port}")
        server.serve_forever()


if __name__ == "__main__":  # pragma: no cover
    run()
