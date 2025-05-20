#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import requests

class MoxaRoamingAnalyzer:
    """
    Analyseur spécialisé dans les problèmes de roaming des appareils Moxa.
    Se concentre sur l'analyse des performances de roaming, des temps de handoff,
    et des configurations optimales pour améliorer la stabilité du roaming.
    """

    def __init__(self):
        # Tenter de charger la clé API depuis le fichier de config
        if os.path.exists('config/api_config.json'):
            try:
                with open('config/api_config.json', 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get('api_key')
            except:
                self.api_key = os.getenv("OPENAI_API_KEY")
        else:
            self.api_key = os.getenv("OPENAI_API_KEY")

    def analyze_logs(self, log_content, current_config):
        """
        Analyse les logs Moxa spécifiquement pour les problèmes de roaming.
        
        Args:
            log_content (str): Contenu des logs à analyser
            current_config (dict): Configuration Moxa actuelle
            
        Returns:
            dict: Résultat de l'analyse avec focus sur le roaming
        """
        if not log_content:
            raise ValueError("Les logs sont vides")

        if not self.api_key:
            raise ValueError("Clé API OpenAI non configurée")

        # Nettoyer et préparer les logs
        clean_logs = log_content.replace("\r\n", "\n").strip()
        
        # Ajouter la configuration actuelle au prompt pour permettre à l'IA de l'évaluer
        config_text = json.dumps(current_config, indent=2)
        
        # Créer le prompt pour l'analyse spécifique au roaming
        prompt = (
            "En tant qu'expert Wi-Fi industriel spécialisé dans le roaming des appareils Moxa, analyser ces logs en détail en recherchant spécifiquement:\n"
            "1. Effet 'ping-pong' : roaming rapide et répété entre les mêmes points d'accès\n"
            "2. Temps de handoff : analyser en détail les temps de transition entre les points d'accès\n"
            "3. Problèmes d'authentification lors du roaming\n"
            "4. Paramètres de roaming inadaptés: seuils, différences, timers\n"
            "5. Problèmes de SNR avant et après le roaming\n\n"
            f"CONFIGURATION ACTUELLE:\n{config_text}\n\n"
            "INSTRUCTIONS IMPORTANTES:\n"
            "1. FOCUS EXCLUSIF SUR LE ROAMING - analyser en profondeur chaque événement de roaming\n"
            "2. Fournir des métriques précises sur les temps de handoff et la fréquence de roaming\n"
            "3. Évaluer si la configuration de roaming est adaptée pour des AMR (robots mobiles)\n"
            "4. Fournir un score global sur 100 pour la performance du roaming\n"
            "5. Fournir une conclusion détaillée sur les performances de roaming\n"
            "6. RÉPONDRE UNIQUEMENT EN FORMAT JSON VALIDE avec la structure suivante:\n"
            "{\n"
            "  \"performance_roaming\": {\n"
            "    \"score\": 0-100,\n"
            "    \"temps_handoff\": {\n"
            "      \"min_ms\": X,\n"
            "      \"max_ms\": Y,\n"
            "      \"moyen_ms\": Z,\n"
            "      \"distribution\": [\"0-50ms: X%\", \"51-100ms: Y%\", \"101-500ms: Z%\", \">500ms: W%\"]\n"
            "    },\n"
            "    \"problemes_detectes\": {\n"
            "      \"ping_pong\": {\n"
            "        \"present\": true|false,\n"
            "        \"occurrences\": X,\n"
            "        \"paires_ap_affectees\": [\"AP1-AP2: X fois\", \"AP2-AP3: Y fois\"],\n"
            "        \"temps_min_entre_roaming\": \"X ms\"\n"
            "      },\n"
            "      \"echecs_roaming\": {\n"
            "        \"total\": X,\n"
            "        \"causes\": [\"timeout_authentification\", \"probleme_association\"],\n"
            "        \"points_acces_problematiques\": [\"MAC_AP1: X echecs\", \"MAC_AP2: Y echecs\"]\n"
            "      },\n"
            "      \"snr_avant_roaming\": {\n"
            "        \"min\": X,\n"
            "        \"max\": Y,\n"
            "        \"moyen\": Z,\n"
            "        \"seuil_critique_atteint\": true|false\n"
            "      },\n"
            "      \"preparation_roaming\": {\n"
            "        \"adequat\": true|false,\n"
            "        \"problemes\": [\"seuil_trop_bas\", \"seuil_trop_eleve\", \"difference_inadequate\"]\n"
            "      }\n"
            "    },\n"
            "    \"parametres_actuels\": {\n"
            "      \"roaming_threshold_type\": \"rssi|snr\",\n"
            "      \"roaming_threshold_value\": X,\n"
            "      \"roaming_difference\": Y,\n"
            "      \"turbo_roaming\": true|false,\n"
            "      \"auth_timeout\": Z\n"
            "    }\n"
            "  },\n"
            "  \"evaluation_configuration\": {\n"
            "    \"adaptee_amr\": true|false,\n"
            "    \"justification\": \"Explication détaillée de l'évaluation\",\n"
            "    \"parametres_optimaux\": {\n"
            "      \"roaming_threshold_type\": \"rssi|snr\",\n"
            "      \"roaming_threshold_value\": X,\n"
            "      \"roaming_difference\": Y,\n"
            "      \"turbo_roaming\": true|false,\n"
            "      \"auth_timeout\": Z\n"
            "    },\n"
            "    \"justifications_parametres\": {\n"
            "      \"roaming_threshold_value\": \"Justification pour cette valeur\",\n"
            "      \"roaming_difference\": \"Justification pour cette valeur\",\n"
            "      \"turbo_roaming\": \"Justification pour ce paramètre\"\n"
            "    }\n"            "  },\n"
            "  \"recommandations\": [\n"
            "    {\n"
            "      \"priorite\": 1-5,\n"
            "      \"probleme\": \"Description concise du problème\",\n"
            "      \"solution\": \"Solution proposée\",\n"
            "      \"impact_estime\": \"Impact estimé sur la performance de roaming\",\n"
            "      \"parametres_a_modifier\": {\n"
            "        \"param1\": \"valeur1\",\n"
            "        \"param2\": \"valeur2\"\n"
            "      }\n"
            "    }\n"
            "  ],\n"
            "  \"analyse_tendances\": {\n"
            "    \"stabilite_roaming\": \"stable|instable|variable\",\n"
            "    \"tendance_degradation\": true|false,\n"
            "    \"facteurs_externes\": [\"interference\", \"surcharge_ap\", \"probleme_configuration\"],\n"
            "    \"heures_problematiques\": [\"HH:MM-HH:MM\"]\n"
            "  },\n"
            "  \"score_global\": 0-100,\n"
            "  \"conclusion\": \"Une conclusion détaillée sur les performances de roaming et les recommandations principales\"\n"
            "}\n\n"
            f"LOGS À ANALYSER:\n{clean_logs}"
        )

        try:
            # Appeler l'API OpenAI
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 2000
                },
                timeout=30  # Timeout de 30 secondes pour éviter les blocages indéfinis
            )

            if response.status_code != 200:
                # Si l'API renvoie une erreur, on lève une exception avec les détails
                error_detail = response.json().get('error', {}).get('message', 'Unknown error')
                raise Exception(f"Erreur API OpenAI ({response.status_code}): {error_detail}")            # Retourner directement la réponse d'OpenAI
            result = response.json()["choices"][0]["message"]["content"]
            
            # Vérifier si le résultat n'est pas vide et qu'il s'agit bien d'un JSON valide
            if not result or not result.strip():
                raise Exception("Réponse vide reçue de l'API OpenAI")
                
            try:
                # Tentative de parsing en mode strict
                parsed_result = json.loads(result)
                return parsed_result
            except json.JSONDecodeError as json_err:
                # En cas d'échec, afficher le contenu reçu dans l'erreur pour faciliter le débogage
                raise Exception(f"Erreur de décodage JSON: {str(json_err)}. Contenu reçu: {result[:200]}...")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur de connexion à l'API OpenAI: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Erreur de décodage JSON: {str(e)}")
        except KeyError as e:
            raise Exception(f"Structure de réponse inattendue de l'API OpenAI: {str(e)}")
        except Exception as e:
            raise Exception(f"Erreur lors de l'analyse des logs de roaming: {str(e)}")
    
    def calculate_roaming_metrics(self, log_content):
        """
        Calcule les métriques spécifiques de roaming à partir des logs Moxa.
        
        Args:
            log_content (str): Contenu des logs à analyser
            
        Returns:
            dict: Métriques de roaming calculées
        """
        metrics = {
            "total_roaming_events": 0,
            "successful_roaming": 0,
            "failed_roaming": 0,
            "handoff_times": [],
            "ping_pong_events": 0,
            "ap_transitions": {}
        }
        
        # Implémentation du calcul des métriques
        # Cette version est simplifiée, une implémentation réelle analyserait
        # les logs ligne par ligne pour extraire les métriques pertinentes
        
        return metrics
    
    def optimize_roaming_parameters(self, metrics, current_config):
        """
        Génère des recommandations optimisées pour les paramètres de roaming
        basées sur les métriques calculées.
        
        Args:
            metrics (dict): Métriques de roaming calculées
            current_config (dict): Configuration Moxa actuelle
            
        Returns:
            dict: Recommandations de paramètres optimisés
        """
        recommendations = {}
        
        # Implémentation des recommandations
        # Cette version est simplifiée, une implémentation réelle analyserait
        # les métriques et générerait des recommandations spécifiques
        
        return recommendations
