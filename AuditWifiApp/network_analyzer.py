#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from wifi.wifi_analyzer import WifiAnalyzer, WifiAnalysis
from wifi.wifi_collector import WifiCollector, WifiSample
from moxa_log_analyzer import MoxaLogAnalyzer

class NetworkAnalyzer:
    """
    Classe qui coordonne l'analyse WiFi en temps réel et l'analyse des logs Moxa
    """

    def __init__(self):
        # Initialisation des analyseurs
        self.wifi_analyzer = WifiAnalyzer()
        self.wifi_collector = WifiCollector()
        self.moxa_analyzer = MoxaLogAnalyzer()

        # État
        self.is_collecting = False
        self.current_wifi_analysis: Optional[WifiAnalysis] = None
        self.current_moxa_analysis = None
        self.last_wifi_samples: List[WifiSample] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Configuration du logging
        self.logger = self._setup_logging()

        # Patterns caractéristiques des logs Moxa
        self.moxa_patterns = [
            "[WLAN] Roaming from AP",
            "Authentication request",
            "Deauthentication from AP",
            "SNR:",
            "Noise floor:",
            "TransferRingToThread",
            "AUTH-RECEIVE",
            "ASSOC-STATE",
            "WLAN-RECEIVE"
        ]

    def _setup_logging(self) -> logging.Logger:
        """Configure le système de journalisation"""
        logger = logging.getLogger('NetworkAnalyzer')
        logger.setLevel(logging.DEBUG)

        # Handler pour fichier
        fh = logging.FileHandler('network_analysis.log', encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # Handler pour console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def start_analysis(self) -> bool:
        """Démarre l'analyse réseau complète"""
        try:
            # Démarrer la collecte WiFi
            if not self.wifi_collector.start_collection():
                self.logger.error("Échec du démarrage de la collecte WiFi")
                return False

            self.is_collecting = True
            self.start_time = datetime.now()
            self.end_time = None
            self.logger.info("Analyse réseau démarrée")
            return True

        except Exception as e:
            self.logger.error(f"Erreur au démarrage de l'analyse: {e}")
            return False

    def stop_analysis(self) -> None:
        """Arrête l'analyse réseau"""
        try:
            if self.is_collecting:
                # Arrêter la collecte WiFi
                samples = self.wifi_collector.stop_collection()

                # Analyser les derniers échantillons
                if samples:
                    self.current_wifi_analysis = self.wifi_analyzer.analyze_samples(samples)
                    self.last_wifi_samples = samples

                self.is_collecting = False
                self.end_time = datetime.now()
                self.logger.info("Analyse réseau arrêtée")
        except Exception as e:
            self.logger.error(f"Erreur à l'arrêt de l'analyse: {e}")

    def analyze_moxa_logs(self, log_content: str) -> dict:
        """
        Analyse les logs Moxa collés.
        Args:
            log_content (str): Contenu des logs à analyser
        Returns:
            dict: Résultat de l'analyse ou None en cas d'erreur
        """
        try:
            # Valider le format des logs
            if not self.validate_moxa_log(log_content):
                self.logger.error("Contenu invalide ou ne ressemblant pas à des logs Moxa")
                return {"error": "Le contenu ne semble pas être des logs Moxa valides"}

            # Prétraiter les logs
            preprocessed_logs = self.preprocess_moxa_log(log_content)
            self.logger.info("Logs prétraités avec succès")

            # Configuration par défaut (à personnaliser plus tard via l'interface)
            default_config = {
                "min_transmission_rate": 6,
                "max_transmission_power": 20,
                "rts_threshold": 512,
                "roaming_mechanism": "signal_strength"
            }

            # Analyser avec l'IA
            analysis_results = self.moxa_analyzer.analyze_logs(preprocessed_logs, default_config)

            if analysis_results:
                self.current_moxa_analysis = analysis_results
                self.logger.info("Analyse des logs Moxa terminée avec succès")
                return analysis_results
            else:
                self.logger.error("L'analyse n'a pas produit de résultats")
                return {"error": "L'analyse n'a pas produit de résultats"}

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse des logs Moxa: {e}")
            return {"error": str(e)}

    def get_combined_report(self) -> Dict:
        """Génère un rapport combiné des analyses WiFi et Moxa"""
        report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "wifi_analysis": None,
            "moxa_analysis": None,
            "recommendations": []
        }

        # Ajouter l'analyse WiFi si disponible
        if self.current_wifi_analysis:
            report["wifi_analysis"] = {
                "signal_strength": {
                    "average": self.current_wifi_analysis.average_signal,
                    "min": self.current_wifi_analysis.min_signal,
                    "max": self.current_wifi_analysis.max_signal
                },
                "quality": {
                    "connection": self.current_wifi_analysis.connection_quality,
                    "stability": self.current_wifi_analysis.signal_stability
                },
                "dropouts": self.current_wifi_analysis.dropout_count
            }

        if self.last_wifi_samples:
            report["ping"] = self._calculate_ping_stats(self.last_wifi_samples)
            report["access_points"] = self._calculate_bssid_stats(self.last_wifi_samples)

        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            report["analysis_duration_seconds"] = int(duration)

        # Ajouter l'analyse Moxa si disponible
        if self.current_moxa_analysis:
            report["moxa_analysis"] = self.current_moxa_analysis

        # Générer des recommandations combinées
        if self.current_wifi_analysis and self.current_moxa_analysis:
            report["recommendations"] = self._generate_combined_recommendations()

        return report

    def _generate_combined_recommendations(self) -> List[str]:
        """Génère des recommandations basées sur les deux analyses"""
        recommendations = []

        # Vérification du signal WiFi
        if self.current_wifi_analysis:
            if self.current_wifi_analysis.dropout_count > 0:
                recommendations.append(
                    "Des déconnexions WiFi ont été détectées. "
                    "Vérifiez la couverture et le placement des points d'accès."
                )

            if self.current_wifi_analysis.signal_stability < 70:
                recommendations.append(
                    "La stabilité du signal est faible. "
                    "Envisagez d'ajuster les paramètres de roaming ou la position des AP."
                )        # Ajouter les recommandations de Moxa
        if self.current_moxa_analysis and isinstance(self.current_moxa_analysis, dict):
            if 'recommendations' in self.current_moxa_analysis:
                recommendations.extend(self.current_moxa_analysis['recommendations'])

        return recommendations

    def _calculate_ping_stats(self, samples: List[WifiSample]) -> Dict[str, float]:
        """Calcule des statistiques de latence et de jitter."""
        latencies = [s.ping_latency for s in samples if s.ping_latency >= 0]
        jitters = [s.jitter for s in samples if s.jitter > 0]

        if not latencies:
            return {}

        return {
            "average_latency": round(sum(latencies) / len(latencies), 1),
            "max_latency": round(max(latencies), 1),
            "min_latency": round(min(latencies), 1),
            "average_jitter": round(sum(jitters) / len(jitters), 1) if jitters else 0.0,
        }

    def _calculate_bssid_stats(self, samples: List[WifiSample]) -> Dict[str, Dict[str, float]]:
        """Calcule des statistiques par point d'accès (BSSID)."""
        stats: Dict[str, Dict[str, Any]] = {}
        for s in samples:
            bssid = getattr(s, "bssid", None)
            if not bssid or bssid in {"00:00:00:00:00:00", "Unknown"}:
                continue

            if bssid not in stats:
                stats[bssid] = {
                    "count": 0,
                    "signals": [],
                    "qualities": [],
                }

            stats[bssid]["count"] += 1
            stats[bssid]["signals"].append(s.signal_strength)
            stats[bssid]["qualities"].append(s.quality)

        result: Dict[str, Dict[str, float]] = {}
        for bssid, data in stats.items():
            result[bssid] = {
                "count": data["count"],
                "average_signal": round(sum(data["signals"]) / len(data["signals"]), 1),
                "min_signal": float(min(data["signals"])),
                "max_signal": float(max(data["signals"])),
                "average_quality": round(sum(data["qualities"]) / len(data["qualities"]), 1),
            }

        return result

    def export_data(self, export_dir: str = "exports") -> str:
        """Exporte toutes les données d'analyse"""
        try:
            # Créer le dossier d'export si nécessaire
            os.makedirs(export_dir, exist_ok=True)

            # Nom de fichier avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(export_dir, f"network_analysis_{timestamp}.json")

            # Générer le rapport complet
            report = self.get_combined_report()

            # Sauvegarder en JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Données exportées vers {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Erreur lors de l'export des données: {e}")
            return ""

    def validate_moxa_log(self, log_content: str) -> bool:
        """Valide que le contenu ressemble à un log Moxa."""
        if not log_content or not isinstance(log_content, str):
            return False

        return any(pattern in log_content for pattern in self.moxa_patterns)

    def preprocess_moxa_log(self, log_content: str) -> str:
        """Prétraite les logs Moxa pour améliorer l'analyse."""
        # Normaliser les sauts de ligne
        log_content = log_content.replace("\r\n", "\n").strip()

        # Supprimer les lignes vides multiples
        log_content = "\n".join(line for line in log_content.split("\n") if line.strip())

        return log_content
