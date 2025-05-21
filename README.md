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
3. Install Node.js (18+), then install the TypeScript tooling and build the extension:
   ```bash
   cd AuditWifiApp
   npm install
   npm run build
   cd ..
   ```
4. Copy `.env.example` to `.env` at the project root and place your API key inside:
   ```bash
   cp .env.example .env
   # then edit .env and set your key
   OPENAI_API_KEY=your-key
   ```
   `.env` is ignored by Git so your key stays local.
5. Launch the user interface:
   ```bash
   python AuditWifiApp/main.py
   ```
5. If you use the bundled VS Code extension, build the TypeScript files first:
   ```bash
   npm install
   npm run compile
   ```

## Configuration

`AuditWifiApp/config.yaml` controls UI options and Wi-Fi thresholds. The new
`wifi_thresholds` section defines when the connection is considered weak or
critical.

```yaml
wifi_thresholds:
  signal:
    weak: -70      # dBm
    critical: -80
  packet_loss:
    warning: 10    # percent
    critical: 20
  latency:
    warning: 100   # ms
    critical: 200
```

## Usage

Start the application with:
```bash
python AuditWifiApp/main.py
```

When analyzing Moxa logs, paste them in the dedicated tab. Optionally fill in
the **Paramètres supplémentaires** field to give extra context to the AI. For
example `roaming=snr` will hint that signal to noise ratio should drive the
roaming logic.

Two buttons help manage the configuration:
* **Copier JSON** copies the current JSON to the clipboard.
* **Exporter JSON** saves it to a file of your choice.

## Running tests

```bash
pytest -v
npm test # run TypeScript unit tests
```

## Repository layout

- `AuditWifiApp/` – main application code
- `AuditWifiApp/tests/` – unit tests
- `requirements.txt` – Python dependencies
- `setup.ps1` / `setup.sh` – install scripts
- `AuditWifiApp/config.yaml` – UI settings and `wifi_thresholds` values
- Backup files from previous versions live in `AuditWifiApp/archive/`

## HistoryManager API

Reports exported from the UI are automatically stored under `AuditWifiApp/logs`
and indexed in `reports.db`. The ``HistoryManager`` class provides a simple API
to manage these records:

- `save_report(report: dict) -> str` – save a report and return the JSON path.
- `list_reports() -> List[dict]` – get all stored reports with their identifier
  and file location.
- `load_report(report_id: int) -> Optional[dict]` – load a report from the
  database.

The UI exposes a new **Historique** tab that lists available reports and lets
you open them with your default viewer.
