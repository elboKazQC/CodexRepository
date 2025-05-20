"""
Module de configuration pour stocker et récupérer la clé API OpenAI.
"""
import os
import json
from pathlib import Path

# Chemin du fichier de configuration
CONFIG_FILE = Path(__file__).parent / "config" / "api_config.json"

def save_api_key(api_key):
    """
    Enregistre la clé API dans le fichier de configuration.
    
    Args:
        api_key (str): La clé API à enregistrer
    """
    # Créer le dossier config s'il n'existe pas
    os.makedirs(Path(CONFIG_FILE).parent, exist_ok=True)
    
    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        except:
            pass  # Utiliser un dictionnaire vide si le fichier est corrompu
    
    config['api_key'] = api_key
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    return True

def get_api_key():
    """
    Récupère la clé API du fichier de configuration.
    
    Returns:
        str: La clé API ou None si non trouvée
    """
    if not CONFIG_FILE.exists():
        return None
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get('api_key')
    except:
        return None