#!/usr/bin/env bash
# Setup script for Codex environment
# Installs Python dependencies using requirements.txt
set -e

# Navigate to repository root
cd "$(dirname "$0")/.."

if [ -d packages ]; then
    pip install --no-index --find-links packages -r requirements.txt
else
    pip install -r requirements.txt
fi
