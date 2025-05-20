"""
Module centralisé pour l'analyse AI des logs et configurations Moxa.
Ce module gère tous les appels à l'API OpenAI liés à l'analyse Moxa.
"""

import os
import json
import requests

class MoxaAIAnalyzer:
    """Analyseur centralisé utilisant l'IA pour toutes les analyses liées à Moxa."""
    
    def __init__(self):
        """Initialise l'analyseur avec la clé API et les paramètres par défaut."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.max_tokens = 2000
        self.temperature = 0.2
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def _call_openai_api(self, prompt):
        """
        Méthode interne pour appeler l'API OpenAI.
        
        Args:
            prompt (str): Le prompt à envoyer à l'API
            
        Returns:
            dict: La réponse parsée de l'API
            
        Raises:
            Exception: Si une erreur survient lors de l'appel API
        """
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                },
                timeout=60
            )

            if response.status_code != 200:
                error_detail = response.json().get('error', {}).get('message', 'Unknown error')
                raise Exception(f"Erreur API OpenAI ({response.status_code}): {error_detail}")

            result = response.json()["choices"][0]["message"]["content"]
            return json.loads(result)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur de connexion à l'API OpenAI: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Erreur de décodage JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Erreur lors de l'appel à l'API: {str(e)}")

    def analyze_logs(self, log_content, current_config):
        """
        Analyse générale des logs Moxa.
        
        Args:
            log_content (str): Contenu des logs à analyser
            current_config (dict): Configuration actuelle du Moxa
            
        Returns:
            dict: Résultats de l'analyse
        """
        prompt = (
            "Analysez ces logs Moxa et fournissez des recommandations d'optimisation.\n\n"
            f"Configuration actuelle:\n{json.dumps(current_config, indent=2)}\n\n"
            f"Logs à analyser:\n{log_content}\n\n"
            "Répondez en JSON avec ce format:\n"
            "{\n"
            "  \"score\": 0-100,\n"
            "  \"metrics\": {\"handoff_time_avg\": \"X ms\", ...},\n"
            "  \"recommendations\": [{\"probleme\": \"\", \"solution\": \"\"}],\n"
            "  \"analysis\": \"Analyse détaillée\"\n"
            "}"
        )
        return self._call_openai_api(prompt)

    def analyze_roaming(self, log_content, current_config):
        """
        Analyse spécifique des performances de roaming.
        
        Args:
            log_content (str): Contenu des logs à analyser
            current_config (dict): Configuration actuelle du Moxa
            
        Returns:
            dict: Résultats de l'analyse de roaming
        """
        prompt = (
            "Analysez les performances de roaming dans ces logs Moxa.\n\n"
            f"Configuration actuelle:\n{json.dumps(current_config, indent=2)}\n\n"
            f"Logs à analyser:\n{log_content}\n\n"
            "Répondez en JSON avec ce format:\n"
            "{\n"
            "  \"roaming_metrics\": {\n"
            "    \"total_events\": 0,\n"
            "    \"avg_handoff_time\": 0,\n"
            "    \"problematic_aps\": []\n"
            "  },\n"
            "  \"recommendations\": []\n"
            "}"
        )
        return self._call_openai_api(prompt)

    def analyze_config(self, config):
        """
        Analyse la configuration Moxa.
        
        Args:
            config (dict): Configuration à analyser
            
        Returns:
            dict: Recommandations d'optimisation de la configuration
        """
        prompt = (
            "Analysez cette configuration Moxa et suggérez des optimisations.\n\n"
            f"Configuration:\n{json.dumps(config, indent=2)}\n\n"
            "Répondez en JSON avec ce format:\n"
            "{\n"
            "  \"score\": 0-100,\n"
            "  \"suggestions\": {\n"
            "    \"param\": {\"valeur\": X, \"justification\": \"...\"}\n"
            "  },\n"
            "  \"recommendations\": []\n"
            "}"
        )
        return self._call_openai_api(prompt)
