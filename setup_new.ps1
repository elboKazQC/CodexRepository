# Setup script for AuditWifiApp
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$VenvPath = ".venv"

Write-Host "Setting up AuditWifiApp development environment..." -ForegroundColor Cyan

# Check Python version
try {
    $version = python --version 2>&1
    if ($version -match "Python (\d+\.\d+)") {
        $currentVersion = $Matches[1]
        if ([version]$currentVersion -ge [version]"3.11") {
            Write-Host "✓ Python $currentVersion found" -ForegroundColor Green
        }
        else {
            throw "Python 3.11 or higher required, found $currentVersion"
        }
    }
}
catch {
    Write-Host "✗ Python not found or version check failed: $_" -ForegroundColor Red
    exit 1
}

# Create/recreate virtual environment
if (Test-Path $VenvPath) {
    if ($Force) {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Path $VenvPath -Recurse -Force
    }
    else {
        Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
    }
}

if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
$activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
}
else {
    Write-Host "✗ Virtual environment activation script not found" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to upgrade pip" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Ensure .env file exists
$envPath = Join-Path "AuditWifiApp" ".env"
if (-not (Test-Path $envPath)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
# Environment variables for AuditWifiApp
OPENAI_API_KEY=
"@ | Set-Content $envPath
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host "! Please set your OPENAI_API_KEY in the .env file" -ForegroundColor Yellow
}

Write-Host "`n✓ Setup completed successfully!" -ForegroundColor Green
Write-Host "To activate the virtual environment again later, run: . $activateScript" -ForegroundColor Cyan
