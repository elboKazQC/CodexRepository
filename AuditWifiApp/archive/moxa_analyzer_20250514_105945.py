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

    def load_memory(self):
        """Charge la mémoire contextuelle depuis un fichier JSON."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as file:
                    return json.load(file)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du chargement de la mémoire Moxa : {str(e)}")
        return []
    
    def save_memory(self, memory):
        """Sauvegarde la mémoire contextuelle dans un fichier JSON."""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, "w", encoding="utf-8") as file:
                json.dump(memory, file, indent=2)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde de la mémoire Moxa : {str(e)}")

    def reset_memory(self):
        """Réinitialise la mémoire contextuelle."""
        if os.path.exists(self.memory_file):
            try:
                os.remove(self.memory_file)
                messagebox.showinfo("Succès", "La mémoire Moxa a été réinitialisée.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la réinitialisation de la mémoire Moxa : {str(e)}")

    def _analyze_log_content(self, log_content):
        """Analyse locale des logs pour extraire les métriques importantes."""
        stats = {
            "handoff_times": [],
            "connection_times": [],
            "ap_connections": {},
            "failed_authentications": 0,
            "roaming_events": 0,
            "problematic_aps": [],
            "total_disconnections": 0,
            "last_roaming_status": None,
            "ping_pong_events": [],  # Nouveau
            "wlan_restarts": 0,      # Nouveau 
            "deauth_requests": [],    # Nouveau
            "snr_drops": [],         # Nouveau
            "auth_timeouts": []      # Nouveau
        }

        lines = log_content.split('\n')
        last_roaming = {}  # Pour détecter les effets ping-pong
        last_ap = None
        last_ap_time = None

        # Patterns étendus pour l'analyse
        handoff_pattern = r"handoff time: (\d+) ms"
        ap_mac_pattern = r"\[([A-F0-9:]+)\]"
        snr_pattern = r"SNR: (\d+)"
        timestamp_pattern = r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})"
        auth_timeout_pattern = r"Authentication request timed out"
        deauth_pattern = r"Received deauth request from ([A-F0-9:]+)"
        wlan_restart_pattern = r"WLAN interface (re)?start"

        for i, line in enumerate(lines):
            try:
                current_timestamp = None
                if timestamp_match := re.search(timestamp_pattern, line):
                    current_timestamp = datetime.strptime(timestamp_match.group(1), "%Y/%m/%d %H:%M:%S")

                # Détecter les redémarrages WLAN
                if re.search(wlan_restart_pattern, line):
                    stats["wlan_restarts"] += 1

                # Détecter les deauth requests
                if deauth_match := re.search(deauth_pattern, line):
                    ap_mac = deauth_match.group(1)
                    stats["deauth_requests"].append({
                        "ap": ap_mac,
                        "timestamp": current_timestamp
                    })                # Détecter les timeouts d'authentification
                auth_timeout_pattern = r"(Authentication response timed out|Connection request.*failed.*Authentication)"
                if re.search(auth_timeout_pattern, line, re.IGNORECASE):
                    stats["failed_authentications"] += 1
                    if current_timestamp:
                        stats["auth_timeouts"].append({
                            "timestamp": current_timestamp
                        })
                        stats["failed_authentications"] += 1

                # Analyser les temps de handoff
                if "handoff time:" in line:
                    if match := re.search(handoff_pattern, line):
                        handoff_time = int(match.group(1))
                        stats["handoff_times"].append(handoff_time)                if handoff_time > 500:  # Seuil critique défini à 500ms
                            # Trouver l'AP concerné dans la ligne
                            if ap_match := re.search(ap_mac_pattern, line):
                                ap_mac = ap_match.group(1)
                                # Ajouter aux APs problématiques avec handoff lent
                                stats["problematic_aps"].append({
                                    "ap_mac": ap_mac,
                                    "issue": f"Handoff critique ({handoff_time} ms)",
                                    "handoff_time": handoff_time,
                                    "severity": "critical"
                                })

                # Analyser les événements de roaming pour détecter les effets ping-pong
                if "Roaming from AP" in line:
                    stats["roaming_events"] += 1
                    stats["last_roaming_status"] = line

                    # Extraire source AP, destination AP et SNR
                    roaming_match = re.search(r"Roaming from AP \[MAC: ([A-F0-9:]+), SNR: (\d+)[^\]]*\] to AP \[MAC: ([A-F0-9:]+), SNR: (\d+)", line)
                    if roaming_match and current_timestamp:
                        source_ap = roaming_match.group(1)
                        source_snr = int(roaming_match.group(2))
                        target_ap = roaming_match.group(3)
                        target_snr = int(roaming_match.group(4))

                        # Détecter les chutes de SNR
                        if source_snr == 0 or source_snr < self.thresholds['low_snr']:
                            stats["snr_drops"].append({
                                "ap": source_ap,
                                "timestamp": current_timestamp,
                                "snr": source_snr
                            })
                            # Ajouter directement à problematic_aps
                            stats["problematic_aps"].append({
                                "ap_mac": source_ap,
                                "issue": "SNR critique",
                                "snr": source_snr,
                                "timestamp": current_timestamp
                            })

                        # Détecter effet ping-pong
                        ap_pair = tuple(sorted([source_ap, target_ap]))
                        if ap_pair in last_roaming:
                            time_diff = (current_timestamp - last_roaming[ap_pair]).total_seconds()
                            if time_diff < self.thresholds['ping_pong_time']:
                                stats["ping_pong_events"].append({
                                    "ap_pair": ap_pair,
                                    "time_diff": time_diff,
                                    "timestamp": current_timestamp
                                })

                        last_roaming[ap_pair] = current_timestamp

                        # Mettre à jour les APs problématiques pour le roaming fréquent
                        for ap_mac in [source_ap, target_ap]:
                            if ap_mac == last_ap and current_timestamp and last_ap_time:
                                time_diff = (current_timestamp - last_ap_time).total_seconds()
                                if time_diff < self.thresholds['min_association']:
                                    stats["problematic_aps"].append({
                                        "ap_mac": ap_mac,
                                        "issue": "Roaming trop fréquent",
                                        "time_diff": time_diff
                                    })

                        last_ap = target_ap
                        last_ap_time = current_timestamp

            except Exception as e:
                print(f"Erreur lors de l'analyse de la ligne: {line}")
                print(f"Exception: {str(e)}")
                continue

        # Agréger et trier les problèmes par AP
        ap_problems = {}
        for ap in stats["problematic_aps"]:
            if ap["ap_mac"] not in ap_problems:
                ap_problems[ap["ap_mac"]] = {
                    "issues": set(),
                    "snr_drops": 0,
                    "handoff_times": [],
                    "deauth_count": 0
                }
            ap_problems[ap["ap_mac"]]["issues"].add(ap.get("issue", "Problème inconnu"))
            if "handoff_time" in ap:
                ap_problems[ap["ap_mac"]]["handoff_times"].append(ap["handoff_time"])

        # Compter les drops de SNR par AP
        for drop in stats["snr_drops"]:
            if drop["ap"] in ap_problems:
                ap_problems[drop["ap"]]["snr_drops"] += 1

        # Compter les deauth par AP
        for deauth in stats["deauth_requests"]:
            if deauth["ap"] in ap_problems:
                ap_problems[deauth["ap"]]["deauth_count"] += 1

        # Mettre à jour la liste des APs problématiques avec les statistiques agrégées
        stats["problematic_aps"] = []
        for ap_mac, data in ap_problems.items():
            severity = "Critique" if data["snr_drops"] > 0 or data["deauth_count"] > 0 else "Important"
            stats["problematic_aps"].append({
                "ap_mac": ap_mac,
                "issues": list(data["issues"]),
                "snr_drops": data["snr_drops"],
                "avg_handoff_time": sum(data["handoff_times"]) / len(data["handoff_times"]) if data["handoff_times"] else 0,
                "deauth_count": data["deauth_count"],
                "severity": severity
            })

        # Calculer les métriques finales
        stats["handoff_time_avg"] = sum(stats["handoff_times"]) / len(stats["handoff_times"]) if stats["handoff_times"] else 0
        stats["handoff_time_std"] = (sum((x - stats["handoff_time_avg"]) ** 2 for x in stats["handoff_times"]) / len(stats["handoff_times"])) ** 0.5 if len(stats["handoff_times"]) > 1 else 0
        stats["roaming_frequency"] = stats["roaming_events"] / (len(lines) / 100)
        stats["instability_score"] = (
            10 * len(stats["ping_pong_events"]) +
            5 * stats["wlan_restarts"] +
            3 * len(stats["deauth_requests"]) +
            2 * len(stats["snr_drops"]) +
            stats["failed_authentications"]
        ) / (len(lines) / 1000)  # Normaliser par millier de lignes

        return stats

    def _calculate_score(self, stats):
        """Calcule un score global basé sur les statistiques."""
        score = 100
        
        # Pénalités étendues pour les problèmes
        if stats["handoff_time_avg"] > self.thresholds['handoff_critical']:
            score -= 25
        elif stats["handoff_time_avg"] > self.thresholds['handoff_warning']:
            score -= 15
        
        # Pénalité pour les ping-pong
        ping_pong_penalty = len(stats["ping_pong_events"]) * 5
        score -= min(30, ping_pong_penalty)  # Maximum 30 points de pénalité
        
        # Pénalité pour les drops de SNR
        snr_drops_penalty = len(stats["snr_drops"]) * 3
        score -= min(20, snr_drops_penalty)  # Maximum 20 points de pénalité
        
        # Pénalité pour les échecs d'authentification et timeouts
        auth_penalty = (stats["failed_authentications"] + len(stats["auth_timeouts"])) * 2
        score -= min(15, auth_penalty)  # Maximum 15 points de pénalité
        
        # Pénalité pour les redémarrages WLAN
        score -= min(20, stats["wlan_restarts"] * 10)  # Maximum 20 points de pénalité
        
        # Pénalité pour les deauth requests
        deauth_penalty = len(stats["deauth_requests"]) * 3
        score -= min(15, deauth_penalty)  # Maximum 15 points de pénalité
        
        return max(0, min(100, score))  # Score entre 0 et 100

    def _generate_recommendations(self, stats, current_config):
        """Génère des recommandations basées sur l'analyse."""
        recommendations = []

        # Recommandations pour le ping-pong
        if len(stats["ping_pong_events"]) > 0:
            recommendations.append({
                "probleme": "Effet ping-pong détecté",
                "impact": "Instabilité de la connexion et latence accrue pour les AMR",
                "solution": "Augmenter le roaming_difference et ajuster les seuils de roaming",
                "parametres": {
                    "roaming_difference": min(current_config.get("roaming_difference", 8) + 3, 15),
                    "roaming_threshold_value": "-65" if current_config.get("roaming_threshold_type") == "signal_strength" else "35"
                }
            })

        # Recommandations pour les drops de SNR
        if len(stats["snr_drops"]) > 0:
            recommendations.append({
                "probleme": "Chutes de SNR avant roaming",
                "impact": "Déconnexions potentielles des AMR",
                "solution": "Ajuster les seuils de roaming et activer le remote connection check",
                "parametres": {
                    "remote_connection_check": True,
                    "roaming_threshold_type": "snr",
                    "roaming_threshold_value": "25"
                }
            })        # Recommandations pour les timeouts d'authentification
        if stats["failed_authentications"] > 0 or len(stats.get("auth_timeouts", [])) > 0:
            recommendations.append({
                "probleme": "Problèmes d'authentification détectés",
                "impact": "Interruptions de service pour les AMR",
                "solution": "Activer le Turbo Roaming et optimiser les timeouts",
                "parametres": {
                    "turbo_roaming": True,
                    "auth_timeout": "1000",
                    "roaming_threshold": "-70"
                }
            })

        # Recommandations pour les handoff lents ou variables
        if stats["handoff_time_avg"] > self.thresholds['handoff_warning'] or stats["handoff_time_std"] > 50:
            recommendations.append({
                "probleme": "Temps de handoff élevés ou variables",
                "impact": "Latence et instabilité pour les AMR",
                "solution": "Optimiser les paramètres de roaming et réduire la fragmentation",
                "parametres": {
                    "min_transmission_rate": max(current_config.get("min_transmission_rate", 6), 12),
                    "fragmentation_threshold": min(current_config.get("fragmentation_threshold", 2346), 1024)
                }
            })

        # Recommandations pour les redémarrages WLAN
        if stats["wlan_restarts"] > 0:
            recommendations.append({
                "probleme": "Redémarrages fréquents de l'interface WLAN",
                "impact": "Interruptions majeures pour les AMR",
                "solution": "Vérifier la stabilité du pilote et réduire la charge réseau",
                "parametres": {
                    "keep_alive_interval": "10",
                    "wmm_enabled": True
                }
            })

        # Recommandations pour les deauth requests
        if len(stats["deauth_requests"]) > 0:
            recommendations.append({
                "probleme": "Déconnexions forcées par les AP",
                "impact": "Interruptions imprévues pour les AMR",
                "solution": "Optimiser la charge des AP et les timeouts",
                "parametres": {
                    "ap_alive_check": True,
                    "max_transmission_power": min(current_config.get("max_transmission_power", 20), 17)
                }
            })

        return recommendations

    def analyze_logs(self, log_content, current_config, analysis_memory):
        """
        Analyse les logs Moxa et fournit des recommandations.
        
        Args:
            log_content (str): Contenu des logs à analyser
            current_config (dict): Configuration actuelle
            analysis_memory (list): Mémoire des analyses précédentes
            
        Returns:
            dict: Résultats de l'analyse
        """
        try:
            # Analyse locale des logs
            stats = self._analyze_log_content(log_content)
            
            # Création du prompt pour l'API
            prompt = (
                "En tant qu'expert en configuration Moxa pour les réseaux Wi-Fi industriels, analysez ces logs en détail.\n\n"
                f"LOGS:\n{log_content}\n\n"
                f"Configuration actuelle:\n{json.dumps(current_config, indent=2)}\n\n"
                "INSTRUCTIONS: Analyser spécifiquement ces problèmes critiques :\n"
                "1. Effet ping-pong: détection des roaming répétés entre mêmes APs (<30 sec)\n"
                "2. Qualité SNR: identifier les cas où SNR=0 avant roaming\n"
                "3. Timeouts: comptabiliser les échecs d'authentification\n"
                "4. Performance roaming: analyser la variance des temps de handoff\n"
                "5. Stabilité interface: détecter redémarrages WLAN fréquents\n"
                "6. Déconnexions forcées: identifier les deauth requests\n\n"
                "FORMAT DE RÉPONSE JSON REQUIS:\n"
                "{\n"
                "  \"analyse_detaillee\": {\n"
                "    \"ping_pong\": {\n"
                "      \"detecte\": true|false,\n"
                "      \"occurrences\": [\"AP1-AP2: X fois en Y sec\", ...],\n"
                "      \"gravite\": 1-10\n"
                "    },\n"
                "    \"problemes_snr\": {\n"
                "      \"aps_snr_zero\": [\"AP: X occurrences\", ...],\n"
                "      \"seuil_roaming_inadapte\": true|false\n"
                "    },\n"
                "    \"timeouts_auth\": {\n"
                "      \"nombre\": X,\n"
                "      \"aps_concernes\": [\"AP: X fois\", ...]\n"
                "    },\n"
                "    \"handoff\": {\n"
                "      \"min_ms\": X,\n"
                "      \"max_ms\": Y,\n"
                "      \"moyenne_ms\": Z,\n"
                "      \"variance_ms\": W\n"
                "    },\n"
                "    \"instabilite_interface\": {\n"
                "      \"redemarrages\": X,\n"
                "      \"interval_moyen_sec\": Y\n"
                "    },\n"
                "    \"deauth_requests\": {\n"
                "      \"nombre\": X,\n"
                "      \"aps_concernes\": [\"AP: X fois\", ...]\n"
                "    }\n"
                "  },\n"
                "  \"score\": 0-100,\n"
                "  \"recommandations\": [\n"
                "    {\n"
                "      \"probleme\": \"description du problème\",\n"
                "      \"impact\": \"impact sur les AMR\",\n"
                "      \"parametres\": {\"param\": \"valeur\"}\n"
                "    }\n"
                "  ],\n"
                "  \"configurations_suggerees\": {\n"
                "    \"param1\": {\"valeur\": X, \"justification\": \"...\"}\n"
                "  }\n"
                "}"
            )
            
            # Appel à l'API GPT-4 pour l'analyse approfondie
            api_results = {}
            if self.api_key:
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
                            "temperature": 0.2,
                            "max_tokens": self.max_tokens
                        }
                    )
                    if response.status_code == 200:
                        api_analysis = response.json()["choices"][0]["message"]["content"]
                        try:
                            api_results = json.loads(api_analysis)
                        except:
                            api_results = {"analysis": api_analysis}
                except Exception as e:
                    api_results = {"error": f"Erreur lors de l'appel API: {str(e)}"}                # Initialisation des metrics si absentes
                stats["handoff_time_avg"] = stats.get("handoff_time_avg", 0)
                stats["roaming_frequency"] = stats.get("roaming_frequency", 0)
                stats["failed_authentications"] = stats.get("failed_authentications", 0)

                # Fusion des recommandations
                stats["recommendations"] = self._generate_recommendations(stats, current_config)
                if "recommendations" in api_results:
                    stats["recommendations"].extend(api_results["recommendations"])
                    # Dédoublonnage des recommandations par problème
                    seen_problems = set()
                    unique_recommendations = []
                    for rec in stats["recommendations"]:
                        if rec["probleme"] not in seen_problems:
                            seen_problems.add(rec["probleme"])
                            unique_recommendations.append(rec)
                    stats["recommendations"] = unique_recommendations

                # Fusion des APs problématiques
                if "problematic_aps" in api_results:
                    for ap in api_results["problematic_aps"]:
                        if not any(p["ap_mac"] == ap["ap_mac"] for p in stats["problematic_aps"]):
                            stats["problematic_aps"].append(ap)
            
            # Combiner les résultats
            score = self._calculate_score(stats)
            results = {
                "score": score,
                "roaming_metrics": {
                    "handoff_time_avg": f"{stats['handoff_time_avg']:.1f} ms",
                    "connection_time_avg": f"{stats['handoff_time_avg'] * 1.2:.1f} ms",
                    "roaming_frequency": f"{stats['roaming_frequency']:.2f} événements/100 lignes",
                    "failed_authentications": stats["failed_authentications"]
                },
                "recommendations": stats.get("recommendations", self._generate_recommendations(stats, current_config)),
                "problematic_aps": stats["problematic_aps"],
                "last_roaming_status": stats["last_roaming_status"],
                "instability_score": stats["instability_score"],
                "analysis": (
                    "Évaluation globale du réseau\n"
                    "---------------------------\n"
                    f"Score global: {score}/100\n\n"
                    "Qualité du roaming:\n"
                    f"- Temps moyen de handoff: {stats['handoff_time_avg']:.1f} ms\n"
                    f"- Fréquence de roaming: {stats['roaming_frequency']:.2f} évts/100 lignes\n"
                    f"- Échecs d'authentification: {stats['failed_authentications']}\n\n"
                    "Points d'attention:\n"
                    f"- Score d'instabilité: {stats['instability_score']:.2f}\n"
                    f"- Nombre de déconnexions: {stats['total_disconnections']}\n"
                    f"- APs problématiques: {len(stats['problematic_aps'])}\n\n"
                    "Analyse IA:\n"
                    f"{api_results.get('analysis', 'Non disponible')}"
                )
            }
            
            return results

        except Exception as e:
            return {
                "error": f"Erreur lors de l'analyse : {str(e)}",
                "score": 0,
                "roaming_metrics": {},
                "recommendations": [],
                "problematic_aps": [],
                "analysis": f"Erreur lors de l'analyse : {str(e)}"
            }
