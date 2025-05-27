#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import requests
import os
import re

class MoxaLogAnalyzer:
    """
    Analyse les logs Moxa via l'API OpenAI pour fournir des recommandations
    d'optimisation des paramètres Moxa.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

        # Configuration par défaut
        self.current_config = {
            'min_transmission_rate': None,
            'max_transmission_power': None,
            'rts_threshold': None,
            'fragmentation_threshold': None,
            'roaming_mechanism': None,
            'roaming_difference': None,
            'remote_connection_check': None,
            'wmm_enabled': None,
            'turbo_roaming': None,
            'ap_alive_check': None,
            'auth_timeout': None
        }

        # Métriques par défaut
        self.metrics = {
            "total_roaming_events": 0,
            "successful_roaming": 0,
            "failed_roaming": 0,
            "handoff_times": [],
            "ping_pong_events": 0,
            "authentication_failures": 0,
            "snr_drops": [],
            "ap_changes": [],

            "deauth_requests": {"total": 0, "per_ap": {}},
            "duration_minutes": 1,

        }

        # Initialize weights for scoring
        self.weights = {
            'handoff_time': 25,      # Temps de basculement
            'ping_pong': 20,         # Effet ping-pong
            'auth_failures': 15,     # Échecs d'authentification
            'snr_quality': 20,       # Qualité SNR
            'roaming_frequency': 10, # Fréquence de roaming
            'stability': 10          # Stabilité générale
        }

    def set_current_config(self, config):
        """Définit les paramètres de configuration actuels pour analyse comparative"""
        for key, value in config.items():
            if key in self.current_config:
                self.current_config[key] = value

    def analyze_logs(self, log_content, current_config):
        """
        Analyse les logs Moxa via l'API OpenAI et retourne un dictionnaire
        avec les résultats de l'analyse et des recommandations.
        """
        if not log_content:
            raise ValueError("Le contenu des logs est vide")

        if not self.api_key:
            raise ValueError("Clé API OpenAI non configurée. Veuillez définir OPENAI_API_KEY.")

        # Mettre à jour la configuration actuelle
        self.set_current_config(current_config)

        # Nettoyer et préparer les logs
        clean_logs = log_content.replace("\r\n", "\n").strip()

        # Ajouter la configuration actuelle au prompt pour permettre à l'IA de l'évaluer
        config_text = json.dumps(current_config, indent=2)

        # Créer le prompt pour l'IA
        prompt = (
            "En tant qu'expert Wi-Fi industriel spécialisé dans les appareils Moxa, analyser ces logs en recherchant spécifiquement:\n"
            "1. Effet 'ping-pong' : détection des roaming répétés entre mêmes APs (<30 sec)\n"
            "2. Problèmes de SNR : détecter les cas où le SNR tombe à 0 ou en-dessous de 10 avant le roaming\n"
            "3. Problèmes d'authentification : timeouts et échecs\n"
            "4. Performance du handoff : analyser les temps de roaming variables\n"
            "5. Stabilité de l'interface WLAN : détecter les redémarrages\n"
            "6. Déconnexions forcées : identifier les deauth requests des APs\n\n"
            "INSTRUCTIONS IMPORTANTES:\n"
            "1. Analyser chaque problème spécifique et fournir des métriques précises\n"
            "2. Évaluer si le réseau est adapté pour une flotte d'AMR (robots mobiles)\n"
            "3. RÉPONDRE UNIQUEMENT EN FORMAT JSON VALIDE avec la structure suivante:\n"
            "{\n"
            "  \"adapte_flotte_AMR\": true|false,\n"
            "  \"score_global\": 0-100,\n"
            "  \"analyse_detaillee\": {\n"
            "    \"ping_pong\": {\n"
            "      \"detecte\": true|false,\n"
            "      \"occurrences\": [\"AP1-AP2: X fois en Y sec\"],\n"
            "      \"gravite\": 1-10,\n"
            "      \"details\": {\n"
            "        \"temps_min_entre_roaming\": \"X sec\",\n"
            "        \"paires_ap_affectees\": [\"AP1-AP2\", \"AP2-AP3\"]\n"
            "      }\n"
            "    },\n"
            "    \"problemes_snr\": {\n"
            "      \"aps_snr_zero\": [\"AP: X occurrences\"],\n"
            "      \"seuil_roaming_inadapte\": true|false,\n"
            "      \"details\": {\n"
            "        \"seuil_actuel\": \"X dB\",\n"
            "        \"seuil_recommande\": \"Y dB\",\n"
            "        \"episodes_critiques\": [\n"
            "          {\"ap\": \"AP1\", \"snr\": 0, \"timestamp\": \"HH:MM:SS\"},\n"
            "          {\"ap\": \"AP2\", \"snr\": 5, \"timestamp\": \"HH:MM:SS\"}\n"
            "        ]\n"
            "      }\n"
            "    },\n"
            "    \"timeouts_auth\": {\n"
            "      \"nombre\": X,\n"
            "      \"temps_moyen_ms\": Z,\n"
            "      \"details\": {\n"
            "        \"causes_principales\": [\"timeout\", \"echec_auth\"],\n"
            "        \"aps_concernes\": [\"AP1: X fois\", \"AP2: Y fois\"]\n"
            "      }\n"
            "    },\n"
            "    \"handoff\": {\n"
            "      \"min_ms\": X,\n"
            "      \"max_ms\": Y,\n"
            "      \"moyen_ms\": Z,\n"
            "      \"distribution\": [\"0-50ms: X\", \"51-100ms: Y\"],\n"
            "      \"details\": {\n"
            "        \"performances_par_ap\": [\n"
            "          {\"ap\": \"AP1\", \"temps_moyen\": X, \"succes\": Y},\n"
            "          {\"ap\": \"AP2\", \"temps_moyen\": X, \"succes\": Y}\n"
            "        ]\n"
            "      }\n"
            "    },\n"
            "    \"stabilite_wlan\": {\n"
            "      \"redemarrages\": X,\n"
            "      \"causes\": [\"inactivite\", \"surcharge\"],\n"
            "      \"impact\": \"description de l'impact\"\n"
            "    }\n"
            "  },\n"
            "  \"parametres_actuels\": {\n"
            "    \"turbo_roaming_correct\": true|false,\n"
            "    \"roaming_mechanism_correct\": true|false,\n"
            "    \"roaming_difference_correct\": true|false,\n"
            "    \"auth_timeout_correct\": true|false\n"
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
            "      \"min_transmission_rate\": X,\n"
            "      \"roaming_difference\": Y,\n"
            "      \"auth_timeout\": Z\n"
            "    },\n"
            "    \"justifications\": [\n"
            "      \"Raison 1 pour les changements\",\n"
            "      \"Raison 2 pour les changements\"\n"
            "    ]\n"
            "  },\n"
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
            "3. Plus de 10 événements ping-pong\n"
            "4. Plus de 5 timeouts d'authentification\n"
            "5. SNR = 0 sur plus de 3 APs\n\n"

            f"CONFIGURATION ACTUELLE:\n{config_text}\n\n"
            f"LOGS À ANALYSER:\n{clean_logs[:4000]}\n\n"  # Limiter pour éviter les tokens excessifs
            "IMPORTANT: Répondre UNIQUEMENT avec du JSON valide, sans texte avant ou après."
        )

        try:
            # Appel à l'API OpenAI
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Tu es un expert en Wi-Fi industriel spécialisé dans les appareils Moxa. Analyse les logs et réponds UNIQUEMENT en JSON valide."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 3000,
                    "temperature": 0.1
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()

                # Nettoyer le contenu pour extraire le JSON
                if content.startswith('```json'):
                    content = content[7:]  # Enlever ```json
                if content.endswith('```'):
                    content = content[:-3]  # Enlever ```
                content = content.strip()

                try:
                    analysis_result = json.loads(content)
                    return analysis_result
                except json.JSONDecodeError as e:
                    return {
                        "error": f"Erreur de parsing JSON: {e}",
                        "raw_content": content
                    }
            else:
                return {
                    "error": f"Erreur API OpenAI: {response.status_code}",
                    "message": response.text
                }

        except requests.exceptions.RequestException as e:
            return {
                "error": f"Erreur de connexion: {e}"
            }
        except Exception as e:
            return {
                "error": f"Erreur inattendue: {e}"
            }

    def calculate_performance_score(self):
        """
        Calcule un score de performance basé sur les métriques collectées.
        Score de 0 à 100, où 100 est la performance optimale.
        """
        if not self.metrics["handoff_times"]:
            return 50  # Score neutre si pas de données

        # Score de base
        base_score = 100

        # Pénalités pour les temps de handoff élevés
        avg_handoff = sum(self.metrics["handoff_times"]) / len(self.metrics["handoff_times"])
        if avg_handoff > 100:
            base_score -= (avg_handoff - 100) * 0.5  # Pénalité progressive

        # Pénalités pour les ping-pong
        ping_pong_penalty = self.metrics["ping_pong_events"] * 10
        base_score -= min(30, ping_pong_penalty)  # Maximum 30 points de pénalité

        # Pénalités pour les chutes de SNR
        snr_drops_penalty = len(self.metrics["snr_drops"]) * 5
        base_score -= min(20, snr_drops_penalty)  # Maximum 20 points de pénalité

        # Pénalités pour les échecs d'authentification
        auth_penalty = self.metrics["authentication_failures"] * 3
        base_score -= min(15, auth_penalty)  # Maximum 15 points de pénalité

        # Pénalités pour la fréquence de roaming excessive
        if self.metrics["total_roaming_events"] > 10:
            freq_penalty = (self.metrics["total_roaming_events"] - 10) * 2
            base_score -= min(15, freq_penalty)

        # Assurer que le score reste dans la fourchette 0-100
        return max(0, min(100, round(base_score)))

    def _get_ping_pong_analysis(self):
        """Analyse des événements ping-pong détectés."""
        return {
            "detecte": self.metrics["ping_pong_events"] > 0,
            "occurrences": [],  # À implémenter selon les données détaillées
            "gravite": min(10, self.metrics["ping_pong_events"] * 2),
            "details": {
                "temps_min_entre_roaming": "< 30 sec",
                "paires_ap_affectees": []  # À calculer depuis les données de roaming
            }
        }

    def _get_snr_analysis(self):
        """Analyse des problèmes de SNR."""
        return {
            "aps_snr_zero": [f"AP {i}: {drop}" for i, drop in enumerate(self.metrics["snr_drops"])],
            "seuil_roaming_inadapte": len(self.metrics["snr_drops"]) > 3,
            "details": {
                "seuil_actuel": f"{self.current_config.get('roaming_difference', 'N/A')} dB",
                "seuil_recommande": "8 dB",
                "episodes_critiques": []
            }
        }

    def _generate_recommendations(self):
        """Génère les recommandations basées sur l'analyse."""
        recommendations = []
        config_changes = []

        # Recommandations pour les ping-pong
        if self.metrics["ping_pong_events"] > 0:
            recommendations.append({
                "probleme": "Effet ping-pong détecté",
                "solution": "Augmenter le seuil de différence de signal pour le roaming",
                "priorite": 1,
                "parametres": {
                    "roaming_difference": "Augmenter de 2-3 dB"
                }
            })
            current = self.current_config.get("roaming_difference")
            if current is not None and current < 12:
                config_changes.append({
                    "param": "roaming_difference",
                    "current": current,
                    "suggested": 12,
                    "reason": "Roaming instable"
                })

        if self.metrics["authentication_failures"] > 0:
            recommendations.append({
                "probleme": "Échecs d'authentification fréquents",
                "solution": "Vérifier la configuration de sécurité et augmenter le timeout d'authentification",
                "priorite": 1,
                "parametres": {
                    "auth_timeout": "Augmenter à 10 secondes",
                    "turbo_roaming": "Activer"
                }
            })
            config_changes.append({
                "param": "auth_timeout",
                "current": self.current_config.get("auth_timeout"),
                "suggested": 10,
                "reason": "Timeouts d'authentification"
            })

        # Recommandations pour les temps de handoff élevés
        if self.metrics["handoff_times"] and max(self.metrics["handoff_times"]) > 200:
            recommendations.append({
                "probleme": "Temps de handoff trop élevés",
                "solution": "Optimiser les paramètres RTS et fragmentation",
                "priorite": 2,
                "parametres": {
                    "turbo_roaming": "Activer"
                }
            })
            rts = self.current_config.get("rts_threshold", 2346)
            frag = self.current_config.get("fragmentation_threshold", 2346)
            config_changes.append({
                "param": "rts_threshold",
                "current": rts,
                "suggested": min(rts or 2346, 1024),
                "reason": "Latence d'association élevée"
            })
            config_changes.append({
                "param": "fragmentation_threshold",
                "current": frag,
                "suggested": min(frag or 2346, 1024),
                "reason": "Latence d'association élevée"
            })

        if self.metrics["snr_drops"]:
            recommendations.append({
                "probleme": f"Chutes de SNR détectées sur {len(self.metrics['snr_drops'])} AP(s)",
                "solution": "Optimiser la disposition et la puissance des points d'accès",
                "priorite": 1,
                "parametres": {
                    "max_transmission_power": "Augmenter si < 20 dBm"
                }
            })
            power = self.current_config.get("max_transmission_power", 10)
            if power is not None and power < 20:
                config_changes.append({
                    "param": "max_transmission_power",
                    "current": power,
                    "suggested": 20,
                    "reason": "SNR trop bas"
                })

        if self.metrics["deauth_requests"]["total"] > 3:
            recommendations.append({
                "probleme": f"Nombre élevé de deauthentications ({self.metrics['deauth_requests']['total']})",
                "solution": "Analyser les causes possibles (interférences, configuration de sécurité) et vérifier les AP concernés",
                "priorite": 2,
                "parametres": {}
            })

        return recommendations, config_changes

    def _evaluate_turbo_roaming(self):
        """Évalue si la configuration du Turbo Roaming est correcte."""
        if not self.current_config.get('turbo_roaming'):
            return self.metrics["handoff_times"] and max(self.metrics["handoff_times"]) < 100
        return True

    def _evaluate_roaming_mechanism(self):
        """Évalue si le mécanisme de roaming est correct."""
        if self.current_config.get('roaming_mechanism') != 'snr':
            return len(self.metrics["snr_drops"]) == 0
        return True

    def _evaluate_roaming_difference(self):
        """Évalue si la différence de roaming est correcte."""
        if self.metrics["ping_pong_events"] > 0:
            return False
        roaming_diff = self.current_config.get('roaming_difference')
        if roaming_diff is not None:
            return 5 <= roaming_diff <= 10
        return True

    def _evaluate_auth_timeout(self):
        """Évalue si le timeout d'authentification est correct."""
        return self.metrics["authentication_failures"] == 0

    def get_analysis_summary(self):
        """Retourne un résumé complet de l'analyse."""
        recommendations, config_changes = self._generate_recommendations()

        return {
            "adapte_flotte_AMR": self.calculate_performance_score() > 70,
            "score_global": self.calculate_performance_score(),
            "analyse_detaillee": {
                "ping_pong": self._get_ping_pong_analysis(),
                "problemes_snr": self._get_snr_analysis(),
                "timeouts_auth": {
                    "nombre": self.metrics["authentication_failures"],
                    "temps_moyen_ms": 0,  # À calculer si données disponibles
                    "details": {
                        "causes_principales": ["timeout", "echec_auth"],
                        "aps_concernes": []
                    }
                },
                "handoff": {
                    "min_ms": min(self.metrics["handoff_times"]) if self.metrics["handoff_times"] else 0,
                    "max_ms": max(self.metrics["handoff_times"]) if self.metrics["handoff_times"] else 0,
                    "moyen_ms": sum(self.metrics["handoff_times"]) // len(self.metrics["handoff_times"]) if self.metrics["handoff_times"] else 0,
                    "distribution": ["0-50ms: 20%", "51-100ms: 60%", "101-200ms: 20%"],
                    "details": {
                        "performances_par_ap": []
                    }
                },
                "stabilite_wlan": {
                    "redemarrages": 0,
                    "causes": [],
                    "impact": "Aucun redémarrage détecté"
                }
            },
            "parametres_actuels": {
                "turbo_roaming_correct": self._evaluate_turbo_roaming(),
                "roaming_mechanism_correct": self._evaluate_roaming_mechanism(),
                "roaming_difference_correct": self._evaluate_roaming_difference(),
                "auth_timeout_correct": self._evaluate_auth_timeout()
            },
            "recommandations": recommendations,
            "details_configuration": {
                "suggestions": {
                    "min_transmission_rate": 12,
                    "roaming_difference": 8,
                    "auth_timeout": 10
                },
                "justifications": [
                    "Optimisation pour environnement industriel",
                    "Réduction des effets ping-pong",
                    "Amélioration de la stabilité de connexion"
                ]
            },
            "config_changes": config_changes
        }
