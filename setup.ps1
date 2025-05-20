<#
    PowerShell setup script for AuditWifiApp.
    Creates a virtual environment and installs packages listed in requirements.txt.
    If a 'packages' directory is present, the script uses it for offline installation.
#>
param(
    [string]$VenvPath = ".venv",
    [string]$PackageDir = "packages"
)

if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
}

. (Join-Path $VenvPath 'Scripts/Activate.ps1')

if (Test-Path $PackageDir) {
    pip install --no-index --find-links $PackageDir -r requirements.txt
}
else {
    pip install -r requirements.txt
}
