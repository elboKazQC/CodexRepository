#Requires -Version 5.0

<#
.SYNOPSIS
    Setup script for AuditWifiApp development environment.
.DESCRIPTION
    This script:
    1. Checks Python installation
    2. Creates a virtual environment
    3. Installs required packages (offline mode if packages directory exists)
    4. Creates .env file if needed
    5. Verifies the installation
#>

[CmdletBinding()]
param(
    [string]$VenvPath = ".venv",
    [string]$PackageDir = "packages",
    [string]$PythonVersion = "3.11",
    [switch]$Force
)

# Function to check if Python is installed with correct version
function Test-PythonInstallation {
    param([string]$RequiredVersion)    try {
        $version = python --version 2>&1
        if ($version -match "Python (\d+\.\d+)") {
            $currentVersion = $Matches[1]
            if ([version]$currentVersion -ge [version]$RequiredVersion) {
                Write-Host "✓ Python $currentVersion found" -ForegroundColor Green
                return $true
            }
        }
        Write-Host "✗ Python $RequiredVersion or higher required, found $currentVersion" -ForegroundColor Red
        return $false
    }
    catch {
        Write-Host "✗ Python not found in PATH" -ForegroundColor Red
        return $false
    }
}
}

# Function to create a virtual environment
function New-VirtualEnvironment {
    param([string]$Path)

    if (Test-Path $Path) {
        if ($Force) {
            Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
            Remove-Item -Path $Path -Recurse -Force
        }
        else {
            Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
            return
        }
    }

    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $Path
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created successfully" -ForegroundColor Green
    }
    else {
        throw "Failed to create virtual environment"
    }
}

# Function to install dependencies
function Install-Dependencies {
    param(
        [string]$RequirementsFile = "requirements.txt",
        [string]$PackageDir
    )

    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    if (Test-Path $PackageDir) {
        Write-Host "Using offline packages from $PackageDir"
        pip install --no-index --find-links $PackageDir -r $RequirementsFile
    }
    else {
        pip install -r $RequirementsFile
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    }
    else {
        throw "Failed to install dependencies"
    }
}

# Function to ensure .env file exists
function Initialize-EnvFile {
    $envPath = Join-Path $PSScriptRoot "AuditWifiApp\.env"
    if (-not (Test-Path $envPath)) {
        Write-Host "Creating .env file..." -ForegroundColor Yellow
        @"
# Environment variables for AuditWifiApp
OPENAI_API_KEY=
"@ | Set-Content $envPath
        Write-Host "✓ Created .env file at $envPath" -ForegroundColor Green
        Write-Host "! Please set your OPENAI_API_KEY in the .env file" -ForegroundColor Yellow
    }
}

# Main setup process
try {
    Write-Host "Setting up AuditWifiApp development environment..." -ForegroundColor Cyan

    if (-not (Test-PythonInstallation -RequiredVersion $PythonVersion)) {
        throw "Python installation check failed"
    }

    New-VirtualEnvironment -Path $VenvPath

    # Activate virtual environment
    $activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    . $activateScript

    Install-Dependencies -RequirementsFile "requirements.txt" -PackageDir $PackageDir

    Initialize-EnvFile

    Write-Host "`n✓ Setup completed successfully!" -ForegroundColor Green
    Write-Host "To activate the virtual environment, run: . $activateScript" -ForegroundColor Cyan
}
catch {
    Write-Host "✗ Setup failed: $_" -ForegroundColor Red
    exit 1
}
