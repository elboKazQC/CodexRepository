"""
Module simplifié pour l'analyse WiFi via OpenAI.
Envoie simplement les données de test WiFi à OpenAI et retourne la réponse brute.
"""

import os
import json
import requests

def analyze_wifi_data(wifi_data):
    """
    Envoie les données de test WiFi à OpenAI pour analyse.
    
    Args:
        wifi_data (dict): Les données WiFi collectées pendant le test
        
    Returns:
        str: La réponse brute d'OpenAI
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("Clé API OpenAI non trouvée dans les variables d'environnement")

    prompt = f"""Analysez ces données de test WiFi collectées sur le terrain.
Identifiez les problèmes de couverture, de signal et de performance.

Données collectées:
{json.dumps(wifi_data, indent=2)}

Veuillez fournir:
1. Une évaluation de la qualité de la couverture WiFi
2. L'identification des zones problématiques
3. Des recommandations pour améliorer la couverture et la performance
4. Une analyse des risques pour les AMR (robots mobiles)"""

    try:
        response = requests.post(
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
            timeout=30
        )

        if response.status_code == 200:
            # Retourne la réponse brute
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Erreur API OpenAI: {response.status_code}")

    except Exception as e:
        raise Exception(f"Erreur lors de l'analyse: {str(e)}")
