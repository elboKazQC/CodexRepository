#!/usr/bin/env bash
set -e

echo "🚀 Création ou activation de l'environnement virtuel..."

VENV=".venv"

if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
    echo "✅ Environnement virtuel créé."
else
    echo "🔁 Environnement virtuel déjà présent."
fi

source "$VENV/bin/activate"
echo "🧠 Environnement activé : $(which python)"

echo "📦 Installation des dépendances en ligne depuis PyPI..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🎉 Setup terminé avec succès!"
