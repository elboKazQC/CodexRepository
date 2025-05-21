#!/usr/bin/env bash
set -e

# Setup script for AuditWifiApp on Linux/macOS.
# Creates the virtual environment, installs Python dependencies and
# prepares the local .env file.

VENV=".venv"
PACKAGES_DIR="packages"
FORCE=0
OFFLINE=0

usage() {
    echo "Usage: $0 [-f] [--offline]"
    echo "  -f        Recreate the virtual environment"
    echo "  --offline Install dependencies from the packages/ directory"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=1
            shift
            ;;
        --offline)
            OFFLINE=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

# Ensure Python 3.11+ is available
python3 - <<'EOF'
import sys
assert sys.version_info >= (3, 11), "Python 3.11 or higher is required"
EOF

if [[ $FORCE -eq 1 && -d "$VENV" ]]; then
    echo "🔄 Removing existing virtual environment..."
    rm -rf "$VENV"
fi

echo "🚀 Création ou activation de l'environnement virtuel..."
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
    echo "✅ Environnement virtuel créé."
else
    echo "🔁 Environnement virtuel déjà présent."
fi

source "$VENV/bin/activate"
echo "🧠 Environnement activé : $(which python)"

pip install --upgrade pip

if [[ $OFFLINE -eq 1 && -d "$PACKAGES_DIR" ]]; then
    echo "📦 Installation des dépendances depuis $PACKAGES_DIR..."
    pip install --no-index --find-links "$PACKAGES_DIR" -r requirements.txt
else
    echo "📦 Installation des dépendances en ligne depuis PyPI..."
    pip install -r requirements.txt
fi

if [ ! -f AuditWifiApp/.env ] && [ -f .env.example ]; then
    cp .env.example AuditWifiApp/.env
    echo "📄 Fichier AuditWifiApp/.env créé. Pensez à définir OPENAI_API_KEY."
fi

echo "🎉 Setup terminé avec succès!"
