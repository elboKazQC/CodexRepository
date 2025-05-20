# -*- coding: utf-8 -*-
import os

def create_file_with_utf8(filename, content):
    """Crée un fichier avec l'encodage UTF-8 et BOM"""
    with open(filename, 'w', encoding='utf-8-sig') as f:
        f.write(content)

def setup():
    # Créer les répertoires nécessaires
    os.makedirs('logs', exist_ok=True)
    os.makedirs('logs_moxa', exist_ok=True)
    os.makedirs('utils', exist_ok=True)

    # Contenu des fichiers
    main_content = '''# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import time
from utils import load_config
from network_scanner import NetworkScanner

# Le reste du code main.py ici
'''

    utils_init_content = '''# -*- coding: utf-8 -*-
import yaml
import os

def load_config():
    """Charge la configuration depuis config.yaml"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
'''

    # Créer les fichiers avec le bon encodage
    create_file_with_utf8('main.py', main_content)
    create_file_with_utf8('utils/__init__.py', utils_init_content)
    
    print("Configuration initiale terminée. Les fichiers ont été créés avec l'encodage UTF-8.")

if __name__ == "__main__":
    setup()