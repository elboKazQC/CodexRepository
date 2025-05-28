"""
Module simplifié pour l'analyse Moxa via OpenAI.
Envoie simplement les logs et la configuration à OpenAI et retourne la réponse brute.

⚠️  ATTENTION DÉVELOPPEURS ⚠️
Ce module contient la logique des instructions personnalisées OpenAI.
TOUTE MODIFICATION du comportement, des prompts ou des paramètres OpenAI
DOIT être accompagnée d'une mise à jour du fichier :
OPENAI_CUSTOM_INSTRUCTIONS_GUIDE.md

Les utilisateurs accèdent à ce guide via le bouton "Guide Instructions OpenAI"
dans l'interface. Le guide doit toujours refléter le comportement réel du code.
"""

import os
import json
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from pathlib import Path

# Import Retry with proper fallback handling
try:
    from urllib3.util.retry import Retry
    RETRY_AVAILABLE = True
except ImportError:
    try:
        from urllib3.util import Retry
        RETRY_AVAILABLE = True
    except ImportError:
        Retry = None
        RETRY_AVAILABLE = False

def create_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    timeout=60
):
    """Crée une session requests avec retry automatique"""
    session = requests.Session()

    if RETRY_AVAILABLE and Retry is not None:
        try:
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
        except Exception:
            # If retry setup fails, continue with basic session
            pass

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

def analyze_moxa_logs(logs, current_config, custom_instructions: str | None = None):
    """
    Envoie les logs Moxa et la configuration à OpenAI pour analyse avec support des instructions personnalisées.

    ⚠️  IMPORTANT - MISE À JOUR DU GUIDE OBLIGATOIRE ⚠️
    Si vous modifiez la logique des instructions personnalisées, le prompt ou les paramètres OpenAI,
    vous DEVEZ mettre à jour le fichier OPENAI_CUSTOM_INSTRUCTIONS_GUIDE.md car les utilisateurs
    y ont accès via le bouton "Guide Instructions OpenAI" dans l'interface.
    Le guide doit refléter exactement le comportement actuel du code.

    Args:
        logs (str): Les logs Moxa à analyser
        current_config (dict): La configuration actuelle du Moxa
        custom_instructions (str, optional): Instructions personnalisées prioritaires pour adapter l'analyse

    Returns:
        str: La réponse d'OpenAI adaptée selon les instructions
    """
    if not logs or not logs.strip():  # Vérifier si les logs sont vides
        raise ValueError("Les logs sont vides")

    api_key = get_api_key()

    # Tronquer les logs si nécessaire
    truncated_logs = truncate_logs(logs)

    # Prompt de base avec les données techniques
    base_prompt = f"""Vous êtes un expert en analyse de logs et configuration réseau WiFi industriel Moxa.

CONFIGURATION ACTUELLE MOXA:
{json.dumps(current_config, indent=2)}

LOGS À ANALYSER:
{truncated_logs}

INSTRUCTIONS DE BASE:
- Analysez les logs en détail
- Identifiez les problèmes de performance, stabilité, sécurité
- Proposez des solutions concrètes d'ajustement de configuration
- Donnez un score global /100 si pertinent
- Soyez précis et actionnable"""    # Adapter le prompt selon les instructions personnalisées
    # ⚠️ RAPPEL: Toute modification ici doit être reflétée dans OPENAI_CUSTOM_INSTRUCTIONS_GUIDE.md
    if custom_instructions and custom_instructions.strip():
        # Nettoyer les instructions par défaut si présentes
        custom_clean = custom_instructions.replace("Exemple: Concentrez-vous sur les problèmes de latence et donnez des solutions prioritaires en format liste numérotée.", "").strip()

        if custom_clean:
            enhanced_prompt = base_prompt + f"""

INSTRUCTIONS PERSONNALISÉES PRIORITAIRES:
{custom_clean}

IMPORTANT: Suivez en priorité les instructions personnalisées ci-dessus.
Vous avez la liberté complète pour:
- Adapter votre style de réponse selon la demande
- Vous concentrer sur des aspects spécifiques demandés
- Utiliser le format de sortie demandé (bullet points, tableaux, listes, etc.)
- Ajouter des analyses non-standard si demandé
- Ignorer certains critères standard si les instructions le précisent
- Ajuster le niveau de détail selon les besoins

Répondez selon ces instructions personnalisées tout en gardant votre expertise technique Moxa."""
        else:
            enhanced_prompt = base_prompt + """

FORMAT DE RÉPONSE STANDARD:
1. Score global (/100)
2. Problèmes identifiés avec priorités
3. Recommandations d'ajustements de configuration
4. Impact attendu des changements
5. Conclusion et prochaines étapes

Soyez détaillé et professionnel."""
    else:
        enhanced_prompt = base_prompt + """

FORMAT DE RÉPONSE STANDARD:
1. Score global (/100)
2. Problèmes identifiés avec priorités
3. Recommandations d'ajustements de configuration
4. Impact attendu des changements
5. Conclusion et prochaines étapes

Soyez détaillé et professionnel."""

    prompt = enhanced_prompt

    session = create_retry_session()

    try:
        response = session.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },            json={
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": "Vous êtes un expert en réseaux WiFi industriels Moxa. Vous pouvez adapter votre analyse selon les besoins spécifiques de l'utilisateur et suivre leurs instructions personnalisées avec flexibilité."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,  # Un peu plus de créativité pour s'adapter aux instructions personnalisées
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
