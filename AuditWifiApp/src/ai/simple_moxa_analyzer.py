"""
Module simplifié pour l'analyse Moxa via OpenAI.
Envoie simplement les logs et la configuration à OpenAI et retourne la réponse brute.
"""

import os
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from pathlib import Path

def create_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    timeout=60
):
    """Crée une session requests avec retry automatique"""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def truncate_logs(logs, max_length=8000):
    """Tronque les logs de manière intelligente pour rester dans les limites de l'API"""
    if len(logs) <= max_length:
        return logs
    
    # Garder le début et la fin des logs
    half_length = max_length // 2
    return f"{logs[:half_length]}\n...[LOGS TRONQUÉS]...\n{logs[-half_length:]}"

def get_api_key():
    """
    Récupère la clé API OpenAI depuis les différentes sources possibles.
    Ordre de priorité:
    1. Variable d'environnement OPENAI_API_KEY
    2. Fichier de configuration config/api_config.json
    """
    # Vérifier la variable d'environnement
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    # Chercher dans le fichier de configuration
    try:
        config_path = Path(__file__).parents[3] / "config" / "api_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                if "api_key" in config:
                    # Définir la variable d'environnement pour les futurs appels
                    os.environ["OPENAI_API_KEY"] = config["api_key"]
                    return config["api_key"]
    except Exception as e:
        print(f"Warning: Could not read API key from config file: {e}")
    
    return None

def analyze_moxa_logs(logs, current_config):
    """
    Envoie les logs Moxa et la configuration à OpenAI pour analyse.
    
    Args:
        logs (str): Les logs Moxa à analyser
        current_config (dict): La configuration actuelle du Moxa
        
    Returns:
        str: La réponse brute d'OpenAI
    """
    if not logs or not logs.strip():  # Vérifier si les logs sont vides
        raise ValueError("Les logs sont vides")
        
    api_key = get_api_key()
    if not api_key:
        raise Exception("Clé API OpenAI non trouvée. Veuillez configurer la variable d'environnement OPENAI_API_KEY ou le fichier config/api_config.json")

    # Tronquer les logs si nécessaire
    truncated_logs = truncate_logs(logs)

    prompt = f"""Analysez ces logs Moxa et la configuration actuelle. 
Identifiez les problèmes et suggérez des ajustements pour optimiser le roaming et la stabilité.

Configuration actuelle:
{json.dumps(current_config, indent=2)}

Logs à analyser:
{truncated_logs}

Donnez une analyse détaillée avec:
1. Les problèmes détectés
2. Les recommandations d'ajustements de configuration
3. Une explication de l'impact attendu de ces changements"""

    session = create_retry_session()

    try:
        response = session.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 2000
            },
            timeout=60  # Augmentation du timeout à 60 secondes
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception("Réponse invalide de l'API OpenAI")
            
    except requests.exceptions.Timeout:
        raise Exception("Le délai d'attente de l'API est dépassé. Essayez avec moins de logs ou réessayez plus tard.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erreur lors de la communication avec l'API OpenAI: {str(e)}")
    except Exception as e:
        raise Exception(f"Erreur inattendue lors de l'analyse: {str(e)}")
