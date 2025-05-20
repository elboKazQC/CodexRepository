#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import requests

class WifiLogAnalyzer:
    """
    Spécialisé dans l'analyse des logs WiFi générés par les ordinateurs portables
    et non par les appareils Moxa. Cet analyseur se concentre sur les problèmes
    de connectivité, de performance et de stabilité WiFi à partir des journaux standards.
    """

    def __init__(self, api_key=None):
        """
        Initialise l'analyseur de logs WiFi avec les paramètres nécessaires.
        
        Args:
            api_key (str, optional): Clé API pour OpenAI. Si non fournie, tente de la récupérer 
                                    depuis les variables d'environnement.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    
    def analyze_logs(self, log_content, current_config):
        """
        Analyse les logs WiFi issus d'un ordinateur portable pour identifier les problèmes
        et générer des recommandations d'optimisation.
        
        Args:
            log_content (str): Contenu des logs à analyser
            current_config (dict): Configuration WiFi actuelle
            
        Returns:
            dict: Résultat de l'analyse contenant les problèmes détectés
                et les recommandations d'optimisation
            
        Raises:
            ValueError: Si les logs sont vides ou la clé API n'est pas configurée
            Exception: En cas d'erreur avec l'API OpenAI ou le traitement des logs
        """
        if not log_content:
            raise ValueError("Les logs sont vides")

        if not self.api_key:
            raise ValueError("Clé API OpenAI non configurée")

        # Nettoyer et préparer les logs
        clean_logs = log_content.replace("\r\n", "\n").strip()
        
        # Ajouter la configuration actuelle au prompt pour permettre à l'IA de l'évaluer
        config_text = json.dumps(current_config, indent=2)
        
        # Créer le prompt pour l'analyse
        prompt = (
            "En tant qu'expert Wi-Fi industriel, analyser ces logs Wi-Fi d'ordinateur portable en détail en recherchant spécifiquement:\n"
            "1. Problèmes de signal: détecter les cas où le signal est faible ou instable\n"
            "2. Problèmes de connexion: timeouts, échecs de connexion, déconnexions\n" 
            "3. Performance réseau: latence, débit, perte de paquets\n"
            "4. Interférences: détection de sources d'interférences potentielles\n"
            "5. Problèmes de configuration: paramètres WiFi inadaptés\n\n"
            f"CONFIGURATION ACTUELLE:\n{config_text}\n\n"
            "INSTRUCTIONS IMPORTANTES:\n"
            "1. Analyser chaque problème spécifique et fournir des métriques précises\n"
            "2. Évaluer si le réseau est adapté pour une flotte d'AMR (robots mobiles)\n"
            "3. Évaluer si chaque paramètre de configuration actuel est correct\n"
            "4. Fournir une conclusion détaillée sur la performance globale\n"
            "5. RÉPONDRE UNIQUEMENT EN FORMAT JSON VALIDE avec la structure suivante:\n"
            "{\n"
            "  \"adapte_flotte_AMR\": true|false,\n"
            "  \"score_global\": 0-100,\n"
            "  \"analyse_detaillee\": {\n"
            "    \"signal\": {\n"
            "      \"niveau_moyen\": \"X dBm\",\n"
            "      \"stabilite\": 1-10,\n"
            "      \"couverture\": \"description de la couverture\",\n"
            "      \"zones_faibles\": [\"zone1\", \"zone2\"]\n"
            "    },\n"
            "    \"connexion\": {\n"
            "      \"deconnexions\": X,\n"
            "      \"echecs\": Y,\n"
            "      \"temps_moyen_connexion\": \"Z ms\",\n"
            "      \"details\": {\n"
            "        \"causes_principales\": [\"timeout\", \"echec_auth\"],\n"
            "        \"frequence\": \"X par heure\"\n"
            "      }\n"
            "    },\n"
            "    \"performance\": {\n"
            "      \"latence_moyenne\": \"X ms\",\n"
            "      \"debit_moyen\": \"Y Mbps\",\n"
            "      \"perte_paquets\": \"Z%\",\n"
            "      \"details\": {\n"
            "        \"variations_latence\": \"description\",\n"
            "        \"impact_debit\": \"description\"\n"
            "      }\n"
            "    },\n"
            "    \"interferences\": {\n"
            "      \"detectees\": true|false,\n"
            "      \"sources_probables\": [\"source1\", \"source2\"],\n"
            "      \"impact\": 1-10,\n"
            "      \"details\": {\n"
            "        \"canaux_affectes\": [1, 6, 11],\n"
            "        \"periodes\": [\"HH:MM-HH:MM\"]\n"
            "      }\n"
            "    },\n"
            "    \"configuration\": {\n"
            "      \"problemes\": [\"probleme1\", \"probleme2\"],\n"
            "      \"details\": {\n"
            "        \"param1\": \"valeur actuelle vs recommandée\",\n"
            "        \"param2\": \"valeur actuelle vs recommandée\"\n"
            "      }\n"
            "    }\n"
            "  },\n"
            "  \"recommandations\": [\n"
            "    {\n"
            "      \"probleme\": \"Description du problème\",\n"
            "      \"solution\": \"Solution proposée\",\n"
            "      \"priorite\": 1-5,\n"
            "      \"parametres\": {\n"
            "        \"param1\": \"valeur1\",\n"
            "        \"param2\": \"valeur2\"\n"
            "      }\n"
            "    }\n"
            "  ],\n"
            "  \"details_configuration\": {\n"
            "    \"suggestions\": {\n"
            "      \"frequence\": \"2.4GHz ou 5GHz\",\n"
            "      \"canal\": X,\n"
            "      \"puissance\": Y\n"            "    },\n"
            "    \"justifications\": [\n"
            "      \"Raison 1 pour les changements\",\n"
            "      \"Raison 2 pour les changements\"\n"
            "    ]\n"
            "  },\n"
            "  \"parametres_actuels\": {\n"
            "    \"frequence_correct\": true|false,\n"
            "    \"canal_correct\": true|false,\n"
            "    \"puissance_correct\": true|false\n"
            "  },\n"
            "  \"conclusion\": \"Une conclusion détaillée sur l'état général de la configuration WiFi et ses implications\"\n"
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
            raise Exception(f"Erreur lors de l'analyse des logs: {str(e)}")
    
    def extract_network_stats(self, log_content):
        """
        Extrait les statistiques réseau des logs WiFi.
        
        Args:
            log_content (str): Contenu des logs à analyser
            
        Returns:
            dict: Statistiques réseau extraites des logs
        """
        stats = {
            "signal_strength": [],
            "latency": [],
            "packet_loss": [],
            "disconnections": 0,
            "connection_attempts": 0
        }
        
        # Implémentation de l'extraction des statistiques
        # Cette version est simplifiée, une implémentation réelle analyserait
        # les logs ligne par ligne pour extraire les métriques pertinentes
        
        return stats
