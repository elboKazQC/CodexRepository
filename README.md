# AuditWifiApp

AuditWifiApp is a Python application for auditing Wi-Fi coverage in factories. It collects signal information, analyses Moxa logs with AI and highlights weak Wi-Fi zones so that AMRs remain connected.

## Setup

1. Install Python 3.11 or newer.
2. Create a virtual environment and install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ./setup.ps1
   ```
   On Linux/macOS you can run `bash setup.sh` instead.
3. Create a `.env` file at the project root containing your API key:
   ```
   OPENAI_API_KEY=your-key
   ```
   The file is ignored by Git so your key persists locally.
4. Launch the user interface:
   ```bash
   python AuditWifiApp/runner.py
   ```

## Running tests

```bash
pytest -v
```

## Repository layout

- `AuditWifiApp/` – main application code
- `AuditWifiApp/tests/` – unit tests
- `requirements.txt` – Python dependencies
- `setup.ps1` / `setup.sh` – install scripts
- `AuditWifiApp/config.yaml` – edit thresholds and UI settings
- Backup files from previous versions live in `AuditWifiApp/archive/`
