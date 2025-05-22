import io
import yaml
import ForkliftInspectionApp.server as server


def run_app(method="GET", data: bytes = b""):
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": "/",
        "CONTENT_LENGTH": str(len(data)),
        "wsgi.input": io.BytesIO(data),
    }
    status_headers = []

    def start_response(status, headers):
        status_headers.append((status, headers))

    body = b"".join(server.app(environ, start_response))
    return status_headers[0][0], body


def test_get_form():
    status, body = run_app()
    assert status.startswith("200")
    assert b"Forklift Inspection Form" in body


def test_post_form(tmp_path, monkeypatch):
    config = {"storage_dir": str(tmp_path), "file_name": "test.csv"}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(config), encoding="utf-8")
    monkeypatch.setattr(server, "DEFAULT_CONFIG_PATH", str(config_path))

    form = b"operator=Bob&forklift_id=FL42&battery_level=90&tires_ok=on&notes=ok"
    status, _ = run_app("POST", form)
    assert status.startswith("200")

    csv_file = tmp_path / "test.csv"
    assert csv_file.exists()
    assert "Bob" in csv_file.read_text()
