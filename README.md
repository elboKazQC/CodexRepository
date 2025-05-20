# AuditWifiApp

AuditWifiApp is a Python application for auditing Wi-Fi coverage in factories. It collects signal information, analyses Moxa logs with AI and highlights weak Wi-Fi zones so that AMRs remain connected. The latest version also suggests concrete updates to your Moxa JSON configuration whenever issues are detected.

## Setup

1. Install Python 3.11 or newer.
2. Create a virtual environment and install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ./setup.ps1
   ```
   On Linux/macOS you can run `bash setup.sh` instead.
3. Copy `.env.example` to `.env` at the project root and place your API key inside:
   ```bash
   cp .env.example .env
   # then edit .env and set your key
   OPENAI_API_KEY=your-key
   ```
   `.env` is ignored by Git so your key stays local.
4. Launch the user interface:
   ```bash
   python AuditWifiApp/runner.py
   ```

## Usage

When analyzing Moxa logs, paste them in the dedicated tab. Optionally fill in
the **Paramètres supplémentaires** field to give extra context to the AI. For
example `roaming=snr` will hint that signal to noise ratio should drive the
roaming logic.

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
