#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import requests

class MoxaLogAnalyzer:
    """
    Analyse les logs Moxa via l'API OpenAI pour fournir des recommandations 
    d'optimisation des paramètres Moxa.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    def analyze_logs(self, log_content, current_config):
        """
        Analyse les logs Moxa via l'API OpenAI.
        
        Args:
            log_content (str): Contenu des logs à analyser
            current_config (dict): Configuration Moxa actuelle
            
        Returns:
            dict: Résultats de l'analyse avec score, recommandations, etc.
        """
        if not log_content:
            raise ValueError("Les logs sont vides")

        if not self.api_key:
            raise ValueError("Clé API OpenAI non configurée")

        # Nettoyer et préparer les logs
        clean_logs = log_content.replace("\r\n", "\n").strip()

        # Créer le prompt pour l'analyse
        prompt = (
            "En tant qu'expert des équipements Moxa, analyser ces logs Wi-Fi et fournir:\n"
            "1. Un score global sur 100\n"
            "2. Une synthèse des métriques de roaming (temps de handoff, fréquence)\n"
            "3. Des recommandations d'optimisation des paramètres Moxa\n"
            "4. Une liste des points d'accès problématiques\n\n"
            
            "PARAMÈTRES AJUSTABLES DU MOXA:\n"
            "- roaming_threshold_value: Seuil de force du signal pour le roaming (en dBm)\n"
            "- roaming_difference: Différence minimale de signal pour le roaming (en dB)\n"
            "- turbo_roaming: Activer/désactiver le roaming rapide\n"
            "- min_transmission_rate: Taux minimum de transmission (en Mbps)\n"
            "- max_transmission_power: Puissance maximale de transmission (en dBm)\n"
            "- rts_threshold: Seuil RTS (Request to Send)\n"
            "- fragmentation_threshold: Seuil de fragmentation\n\n"
            
            "FORMAT DE RÉPONSE ATTENDU (JSON):\n"
            "{\n"
            "  \"score\": 0-100,\n"
            "  \"roaming_metrics\": {\n"
            "    \"handoff_time_avg\": \"X ms\",\n"
            "    \"connection_time_avg\": \"X ms\",\n"
            "    \"roaming_frequency\": \"X événements/100 lignes\",\n"
            "    \"failed_authentications\": X\n"
            "  },\n"
            "  \"recommendations\": [\n"
            "    {\n"
            "      \"probleme\": \"Description du problème\",\n"
            "      \"impact\": \"Impact sur les AMR\",\n"
            "      \"solution\": \"Solution proposée\",\n"
            "      \"parametres\": {\"param1\": \"valeur1\"}\n"
            "    }\n"
            "  ],\n"
            "  \"problematic_aps\": [\n"
            "    {\n"
            "      \"ap_mac\": \"XX:XX:XX:XX:XX:XX\",\n"
            "      \"issues\": [\"problème 1\", \"problème 2\"],\n"
            "      \"occurrences\": X,\n"
            "      \"avg_snr\": Y\n"
            "    }\n"
            "  ],\n"
            "  \"analysis\": \"Analyse détaillée en français\"\n"
            "}\n\n"
            
            "CRITÈRES D'INVALIDITÉ:\n"
            "1. Score = 0/100\n"
            "2. Temps de handoff > 500ms\n"
            "3. Plus de 10 échecs d'authentification\n"
            "4. Plus de 3 APs avec SNR = 0\n"
            "Si un de ces critères est détecté, ajouter un champ 'valid: false' dans la réponse\n\n"
            
            f"CONFIGURATION ACTUELLE:\n{json.dumps(current_config, indent=2)}\n\n"
            f"LOGS À ANALYSER:\n{clean_logs}"
        )

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
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

            if response.status_code != 200:
                raise Exception(f"Erreur API ({response.status_code}): {response.text}")

            # Extraire et valider la réponse JSON
            result = response.json()["choices"][0]["message"]["content"]
            analysis = json.loads(result)

            # Valider que la réponse contient les champs requis
            required_fields = ["score", "roaming_metrics", "recommendations", "problematic_aps", "analysis"]
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"Réponse API invalide: champ '{field}' manquant")

            return analysis

        except requests.exceptions.Timeout:
            raise Exception("Délai d'attente dépassé pour l'analyse")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur de communication avec l'API: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Erreur de parsing JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Erreur lors de l'analyse: {str(e)}")
