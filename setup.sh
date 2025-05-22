#!/usr/bin/env bash
# Simple setup script to install dependencies into a virtual environment
set -e
VENV=.venv
if [ ! -d "$VENV" ]; then
    python -m venv $VENV
fi
source $VENV/bin/activate
if [ -d packages ]; then
    pip install --no-index --find-links packages -r requirements.txt
else
    pip install -r requirements.txt
fi
