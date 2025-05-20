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
            'ap_alive_check': None
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
            'auth_failures': 15,      # Échecs d'authentification
            'snr_quality': 25,       # Qualité du signal
            'roaming_stability': 15   # Stabilité générale
        }

        self._reset_metrics()

    def analyze_logs(self, log_content, current_config=None):
        """
        Analyse les logs Moxa et retourne les résultats structurés.

        Args:
            log_content (str): Contenu brut des logs Moxa
            current_config (dict): Configuration actuelle des paramètres Moxa

        Returns:
            dict: Résultats de l'analyse avec la structure suivante:
                {
                    "score_global": int,
                    "analyse_detaillee": {
                        "ping_pong": {...},
                        "handoff": {...},
                        "problemes_snr": {...}
                    },
                    "recommandations": [...]
                }
        """
        try:
            # Mise à jour de la configuration si fournie
            if current_config:
                self.current_config.update(current_config)

            # Réinitialiser les métriques
            self._reset_metrics()

            # Analyser les logs ligne par ligne
            for line in log_content.split('\n'):
                self._process_log_line(line)

            # Analyse basique des métriques
            self._analyze_basic_metrics(log_content)

            # Calculer les métriques dérivées
            self._calculate_derived_metrics()

            # Préparer les résultats finaux
            score = self._calculate_score()
            details = self._get_detailed_analysis()
            recommendations, config_changes = self._generate_recommendations()

            return {
                "score_global": score,
                "analyse_detaillee": {
                    "ping_pong": details["ping_pong"],
                    "handoff": details["handoff"],
                    "problemes_snr": details["problemes_snr"],
                    "authentification": {
                        "timeouts": self.metrics["authentication_failures"],
                        "echecs": self.metrics["authentication_failures"],
                        "temps_moyen_ms": sum(self.metrics["handoff_times"])/len(self.metrics["handoff_times"]) if self.metrics["handoff_times"] else 0,
                        "details": {
                            "causes_principales": ["timeout", "echec_auth"] if self.metrics["authentication_failures"] > 0 else [],
                            "aps_concernes": []  # À remplir avec les AP problématiques
                        }
                    },
                    "stabilite_wlan": {
                        "redemarrages": 0,  # À implémenter détection des redémarrages
                        "intervalle_moyen_min": 0,
                        "details": {
                            "causes": ["driver", "ap_disconnect"] if self.metrics["failed_roaming"] > 0 else [],
                            "timestamps": []  # À remplir avec les timestamps des événements
                        }
                    },
                    "deauth_requests": {
                        "total": self.metrics["deauth_requests"]["total"],
                        "par_ap": self.metrics["deauth_requests"]["per_ap"],
                        "details": {
                            "raisons": ["inactivite", "surcharge"] if self.metrics["failed_roaming"] > 0 else [],
                            "impact": "À évaluer selon le nombre d'événements"
                        }
                    }
                },
                "recommandations": recommendations,
                "config_changes": config_changes,
                "parametres_actuels": {
                    "turbo_roaming_correct": self._evaluate_turbo_roaming(),
                    "roaming_mechanism_correct": self._evaluate_roaming_mechanism(),
                    "roaming_difference_correct": self._evaluate_roaming_difference(),
                    "auth_timeout_correct": self.metrics["authentication_failures"] == 0
                }
            }
        except Exception as e:
            return {
                "error": f"Erreur lors de l'analyse: {str(e)}",
                "score_global": 0,
                "analyse_detaillee": {},
                "recommandations": [],
                "config_changes": []
            }

    def _reset_metrics(self):
        """Réinitialise toutes les métriques à leurs valeurs par défaut."""
        self.metrics = {
            "total_roaming_events": 0,
            "successful_roaming": 0,
            "failed_roaming": 0,
            "handoff_times": [],
            "ping_pong_events": 0,
            "authentication_failures": 0,
            "roaming_success_rate": 0,
            "snr_drops": [],
            "ap_changes": [],

            "deauth_requests": {"total": 0, "per_ap": {}},
            "duration_minutes": 1,

        }

    def _process_log_line(self, line):
        """
        Traite une ligne de log et met à jour les métriques appropriées.

        Args:
            line (str): La ligne de log à analyser
        """
        line = line.lower()  # Convertir en minuscules pour faciliter la recherche

        # Détecter les événements de roaming
        if "roaming" in line:
            self.metrics["total_roaming_events"] += 1
            if "successful" in line or "completed" in line:
                self.metrics["successful_roaming"] += 1
                # Extraire le temps de handoff s'il est présent
                if "handoff time:" in line:
                    try:
                        time_str = line.split("handoff time:")[1].split("ms")[0].strip()
                        self.metrics["handoff_times"].append(int(time_str))
                    except:
                        pass
            elif "failed" in line or "timeout" in line:
                self.metrics["failed_roaming"] += 1

            # Extraire les informations SNR
            if "snr:" in line:
                try:
                    snr_str = line.split("snr:")[1].split("]")[0].strip()
                    snr = int(snr_str)
                    if snr <= 10:  # SNR critique
                        self.metrics["snr_drops"].append({
                            "value": snr,
                            "ap": line.split("[mac:")[1].split("]")[0].strip() if "[mac:" in line else "unknown"
                        })
                except:
                    pass

        # Détecter les échecs d'authentification
        if "authentication failed" in line or "auth failed" in line:
            self.metrics["authentication_failures"] += 1

        # Détecter les changements d'AP
        if "ap changed" in line or "connected to ap" in line:
            if "[mac:" in line:
                try:
                    ap_mac = line.split("[mac:")[1].split("]")[0].strip()
                    self.metrics["ap_changes"].append({
                        "ap": ap_mac,
                        "timestamp": line.split()[0] if " " in line else "unknown"
                    })
                    # Détecter le ping-pong
                    self._check_ping_pong(ap_mac)
                except:
                    pass

    def _check_ping_pong(self, ap_mac):
        """
        Vérifie si un changement d'AP correspond à un effet ping-pong.
        """
        if len(self.metrics["ap_changes"]) >= 2:
            previous = self.metrics["ap_changes"][-2]["ap"]
            if previous == ap_mac:  # Retour à l'AP précédent
                self.metrics["ping_pong_events"] += 1

    def _calculate_derived_metrics(self):
        """Calcule les métriques dérivées basées sur les métriques de base."""
        total = self.metrics["total_roaming_events"]
        if total > 0:
            self.metrics["roaming_success_rate"] = (self.metrics["successful_roaming"] / total) * 100
        else:
            self.metrics["roaming_success_rate"] = 0

    def _analyze_basic_metrics(self, log_content):
        """
        Analyse les métriques de base dans les logs bruts.
        """
        lines = log_content.split('\n')

        # Analyser des blocs de texte pour une meilleure détection des événements liés
        for i in range(len(lines)):
            line = lines[i].lower()
            # Analyser le contexte autour des événements de roaming
            if "roaming" in line:
                context = "\n".join(lines[max(0, i-5):min(len(lines), i+5)])
                self._analyze_roaming_context(context)

    def _analyze_roaming_context(self, context):
        """
        Analyse le contexte d'un événement de roaming pour extraire plus d'informations.
        """
        if "authentication timeout" in context.lower():
            self.metrics["authentication_failures"] += 1

        if "deauthentication" in context.lower() or "deauth request" in context.lower():
            for line in context.split("\n"):
                lowered = line.lower()
                if "deauthentication" in lowered or "deauth request" in lowered:
                    self.metrics["deauth_requests"]["total"] += 1
                    mac = None
                    if "[mac:" in lowered:
                        mac = lowered.split("[mac:")[1].split("]")[0].strip()
                    else:
                        mac_match = re.search(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", lowered)
                        if mac_match:
                            mac = mac_match.group(0)
                    if mac:
                        self.metrics["deauth_requests"]["per_ap"].setdefault(mac, 0)
                        self.metrics["deauth_requests"]["per_ap"][mac] += 1

    def _calculate_score(self):
        """Calcule un score global basé sur les métriques avec un système pondéré."""
        total_score = 0

        # 1. Évaluation des temps de handoff (25 points)
        if self.metrics["handoff_times"]:
            avg_handoff = sum(self.metrics["handoff_times"]) / len(self.metrics["handoff_times"])
            if avg_handoff <= 50:  # Excellent: ≤ 50ms
                total_score += self.weights['handoff_time']
            elif avg_handoff <= 100:  # Bon: 51-100ms
                total_score += self.weights['handoff_time'] * 0.8
            elif avg_handoff <= 200:  # Moyen: 101-200ms
                total_score += self.weights['handoff_time'] * 0.5
            else:  # Faible: > 200ms
                total_score += self.weights['handoff_time'] * 0.2

        # 2. Évaluation ping-pong (20 points)
        ping_pong_score = self.weights['ping_pong']
        if self.metrics["ping_pong_events"] > 0:
            ping_pong_score *= max(0, 1 - (self.metrics["ping_pong_events"] * 0.2))
        total_score += ping_pong_score

        # 3. Évaluation authentification (15 points)
        auth_score = self.weights['auth_failures']
        if self.metrics["authentication_failures"] > 0:
            auth_score *= max(0, 1 - (self.metrics["authentication_failures"] * 0.25))
        total_score += auth_score

        # 4. Évaluation SNR (25 points)
        snr_score = self.weights['snr_quality']
        if self.metrics["snr_drops"]:
            snr_score *= max(0, 1 - (len(self.metrics["snr_drops"]) * 0.15))
        total_score += snr_score

        # 5. Stabilité générale (15 points)
        stability_score = self.weights['roaming_stability']
        total_events = sum([
            len(self.metrics["handoff_times"]),
            self.metrics["ping_pong_events"],
            self.metrics["authentication_failures"],
            len(self.metrics["snr_drops"])
        ])

        if total_events > 0:
            # Pénaliser si trop d'événements par rapport à la durée analysée
            events_per_minute = total_events / max(1, self.metrics["duration_minutes"])
            if events_per_minute > 2:  # Plus de 2 événements par minute
                stability_score *= max(0, 1 - ((events_per_minute - 2) * 0.2))

        total_score += stability_score

        return max(0, min(100, round(total_score)))

    def _get_detailed_analysis(self):
        """Génère l'analyse détaillée basée sur les métriques."""
        handoff_times = self.metrics["handoff_times"]
        snr_issues = [f"AP {drop['ap']}: SNR {drop['value']} dB" for drop in self.metrics["snr_drops"]]

        return {
            "ping_pong": {
                "detecte": self.metrics["ping_pong_events"] > 0,
                "occurrences": [f"Détecté {self.metrics['ping_pong_events']} fois"],
                "gravite": min(10, self.metrics["ping_pong_events"] * 2),
                "details": {
                    "temps_min_entre_roaming": "10 sec",  # À calculer à partir des timestamps
                    "paires_ap_affectees": self._get_ping_pong_pairs()
                }
            },
            "handoff": {
                "min_ms": min(handoff_times) if handoff_times else "N/A",
                "max_ms": max(handoff_times) if handoff_times else "N/A",
                "moyen_ms": sum(handoff_times)/len(handoff_times) if handoff_times else "N/A",
                "distribution": self._calculate_handoff_distribution(handoff_times)
            },
            "problemes_snr": {
                "aps_snr_zero": snr_issues,
                "seuil_roaming_inadapte": len(snr_issues) > 0
            }
        }

    def _get_ping_pong_pairs(self):
        """Retourne les paires d'AP impliquées dans des effets ping-pong."""
        pairs = []
        changes = self.metrics["ap_changes"]
        for i in range(len(changes) - 1):
            if i + 1 < len(changes) and changes[i]["ap"] == changes[i+1]["ap"]:
                if i > 0:
                    pair = f"{changes[i-1]['ap']}-{changes[i]['ap']}"
                    if pair not in pairs:
                        pairs.append(pair)
        return pairs

    def _calculate_handoff_distribution(self, handoff_times):
        """Calcule la distribution des temps de handoff."""
        if not handoff_times:
            return []

        distribution = {
            "0-50ms": 0,
            "51-100ms": 0,
            "101-200ms": 0,
            ">200ms": 0
        }

        for time in handoff_times:
            if time <= 50:
                distribution["0-50ms"] += 1
            elif time <= 100:
                distribution["51-100ms"] += 1
            elif time <= 200:
                distribution["101-200ms"] += 1
            else:
                distribution[">200ms"] += 1

        return [f"{k}: {v}" for k, v in distribution.items() if v > 0]

    def _generate_recommendations(self):
        """Génère des recommandations basées sur l'analyse."""
        recommendations = []
        config_changes = []

        if self.metrics["ping_pong_events"] > 0:
            recommendations.append({
                "probleme": "Effet ping-pong détecté",
                "solution": "Augmenter le seuil de différence de signal pour le roaming",
                "priorite": 1,
                "parametres": {
                    "roaming_difference": "Augmenter de 2-3 dB"
                }
            })
            current = self.current_config.get("roaming_difference", 8)
            if current < 12:
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
                "reason": "Échecs d'authentification"
            })

        if self.metrics["handoff_times"]:
            avg_handoff = sum(self.metrics["handoff_times"]) / len(self.metrics["handoff_times"])
            if avg_handoff > 100:
                recommendations.append({
                    "probleme": f"Temps de handoff élevé (moyenne: {avg_handoff:.1f}ms)",
                    "solution": "Activer Turbo Roaming et optimiser la disposition des points d'accès",
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
                    "suggested": min(rts, 1024),
                    "reason": "Latence d'association élevée"
                })
                config_changes.append({
                    "param": "fragmentation_threshold",
                    "current": frag,
                    "suggested": min(frag, 1024),
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
            if power < 20:
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
        if self.current_config.get('roaming_difference'):
            return 5 <= self.current_config['roaming_difference'] <= 10
        return True
