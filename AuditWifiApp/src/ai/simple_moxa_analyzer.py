"""
Module simplifié pour l'analyse Moxa via OpenAI.
Envoie simplement les logs et la configuration à OpenAI et retourne la réponse brute.
"""

import os
import json
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from pathlib import Path
from typing import Optional


def _sanitize_additional_params(params: str, max_length: int = 500) -> str:
    """Return params stripped of non-printable chars and validated by length."""
    cleaned = "".join(ch for ch in params if ch.isprintable())
    if len(cleaned) > max_length:
        raise ValueError(
            f"Paramètres supplémentaires trop longs (max {max_length} caractères)"
        )
    return cleaned

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

def _log_error(msg: str) -> None:
    """Append API errors to api_errors.log."""
    try:
        with open("api_errors.log", "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} - SIMPLE_MOXA_ANALYZER - {msg}\n")
    except Exception:
        pass

def truncate_logs(logs, max_length=8000):
    """Tronque les logs de manière intelligente pour rester dans les limites de l'API"""
    if len(logs) <= max_length:
        return logs
    
    # Garder le début et la fin des logs
    half_length = max_length // 2
    return f"{logs[:half_length]}\n...[LOGS TRONQUÉS]...\n{logs[-half_length:]}"

def get_api_key():
    """Retourne la clé API OpenAI depuis la variable d'environnement."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception(
            "Clé API OpenAI non trouvée. Définissez la variable d'environnement OPENAI_API_KEY."
        )
    return api_key

def analyze_moxa_logs(logs, current_config, additional_params: str | None = None):
    """
    Envoie les logs Moxa et la configuration à OpenAI pour analyse.
    
    Args:
        logs (str): Les logs Moxa à analyser
        current_config (dict): La configuration actuelle du Moxa
        additional_params (str | None): Informations facultatives fournies par
            l'utilisateur pour préciser la configuration ou le contexte.
        
    Returns:
        str: La réponse brute d'OpenAI
    """
    if not logs or not logs.strip():  # Vérifier si les logs sont vides
        raise ValueError("Les logs sont vides")
        
    api_key = get_api_key()

    # Tronquer les logs si nécessaire
    truncated_logs = truncate_logs(logs)

    sanitized_params: Optional[str] = None
    if additional_params:
        sanitized_params = _sanitize_additional_params(additional_params)

    extra = f"\nParamètres supplémentaires:\n{sanitized_params}" if sanitized_params else ""

    prompt = f"""Analysez ces logs Moxa et la configuration actuelle.
Identifiez les problèmes et suggérez des ajustements pour optimiser le roaming et la stabilité.

Configuration actuelle:
{json.dumps(current_config, indent=2)}{extra}

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
            timeout=60
        )

        if response.status_code != 200:
            error_detail = response.json().get('error', {}).get('message', '')
            msg = f"Erreur API OpenAI ({response.status_code}): {error_detail}"
            _log_error(msg)
            raise Exception(msg)

        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            msg = "Réponse invalide de l'API OpenAI"
            _log_error(msg)
            raise Exception(msg)

    except requests.exceptions.Timeout:
        msg = (
            "Le délai d'attente de l'API OpenAI est dépassé. "
            "Essayez avec moins de logs ou réessayez plus tard."
        )
        _log_error(msg)
        raise Exception(msg)
    except requests.exceptions.ConnectionError:
        msg = (
            "Impossible de contacter le service OpenAI. "
            "Vérifiez votre connexion internet ou votre clé API."
        )
        _log_error(msg)
        raise Exception(msg)
    except requests.exceptions.RequestException as e:
        msg = f"Erreur lors de la communication avec l'API OpenAI: {str(e)}"
        _log_error(msg)
        raise Exception(msg)
    except json.JSONDecodeError:
        msg = "Réponse invalide de l'API OpenAI"
        _log_error(msg)
        raise Exception(msg)
    except Exception as e:
        msg = f"Erreur inattendue lors de l'analyse: {str(e)}"
        _log_error(msg)
        raise Exception(msg)
