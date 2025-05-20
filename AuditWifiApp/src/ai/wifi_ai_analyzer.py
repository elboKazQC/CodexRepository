"""
Module centralisé pour l'analyse AI des données WiFi.
Ce module gère tous les appels à l'API OpenAI liés à l'analyse WiFi.
"""

import os
import json
import requests

class WifiAIAnalyzer:
    """Analyseur centralisé utilisant l'IA pour toutes les analyses liées au WiFi."""
    
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

    def analyze_signals(self, data, thresholds=None):
        """
        Analyse des signaux WiFi.
        
        Args:
            data (dict): Données des signaux WiFi à analyser
            thresholds (dict, optional): Seuils personnalisés pour l'analyse
            
        Returns:
            dict: Résultats de l'analyse des signaux
        """
        prompt = (
            "Analysez ces données de signal WiFi pour détecter les problèmes potentiels.\n\n"
            f"Données:\n{json.dumps(data, indent=2)}\n\n"
            f"Seuils:\n{json.dumps(thresholds, indent=2) if thresholds else 'Seuils par défaut'}\n\n"
            "Répondez en JSON avec ce format:\n"
            "{\n"
            "  \"signal_quality\": \"good|medium|poor\",\n"
            "  \"metrics\": {\"avg_signal\": -XX, \"stability\": X},\n"
            "  \"risk_zones\": [{\"location\": \"\", \"issues\": []}],\n"
            "  \"recommendations\": []\n"
            "}"
        )
        return self._call_openai_api(prompt)

    def analyze_coverage(self, data):
        """
        Analyse de la couverture WiFi.
        
        Args:
            data (dict): Données de couverture WiFi à analyser
            
        Returns:
            dict: Résultats de l'analyse de couverture
        """
        prompt = (
            "Analysez ces données de couverture WiFi pour identifier les zones problématiques.\n\n"
            f"Données:\n{json.dumps(data, indent=2)}\n\n"
            "Répondez en JSON avec ce format:\n"
            "{\n"
            "  \"coverage_score\": 0-100,\n"
            "  \"coverage_map\": {\n"
            "    \"good_zones\": [],\n"
            "    \"weak_zones\": [],\n"
            "    \"dead_zones\": []\n"
            "  },\n"
            "  \"recommendations\": []\n"
            "}"
        )
        return self._call_openai_api(prompt)

    def analyze_performance(self, data):
        """
        Analyse des performances WiFi.
        
        Args:
            data (dict): Données de performance WiFi à analyser
            
        Returns:
            dict: Résultats de l'analyse des performances
        """
        prompt = (
            "Analysez ces données de performance WiFi.\n\n"
            f"Données:\n{json.dumps(data, indent=2)}\n\n"
            "Répondez en JSON avec ce format:\n"
            "{\n"
            "  \"performance_score\": 0-100,\n"
            "  \"metrics\": {\n"
            "    \"latency\": \"X ms\",\n"
            "    \"packet_loss\": \"X%\",\n"
            "    \"interference_level\": \"low|medium|high\"\n"
            "  },\n"
            "  \"issues\": [],\n"
            "  \"recommendations\": []\n"
            "}"
        )
        return self._call_openai_api(prompt)
