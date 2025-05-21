#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

from wifi.wifi_analyzer import WifiAnalyzer, WifiAnalysis
from wifi.wifi_collector import WifiCollector, WifiSample
from moxa_log_analyzer import MoxaLogAnalyzer
from config_manager import ConfigurationManager
from app_config import Constants

from history_manager import HistoryManager


class NetworkAnalyzer:
    """
    Classe qui coordonne l'analyse WiFi en temps réel et l'analyse des logs Moxa.
    """

    def __init__(self, config_manager: Optional[ConfigurationManager] = None):
        """
        Initialise les analyseurs avec la configuration fournie.
        """
        self.config_manager = config_manager or ConfigurationManager(path=Constants.CONFIG_PATH)
        cfg = self.config_manager.get_config().get("network_analyzer", {})

        # Initialisation des analyseurs
        self.wifi_analyzer = WifiAnalyzer()
        self.wifi_collector = WifiCollector()
        self.moxa_analyzer = MoxaLogAnalyzer()

        # État
        self.is_collecting = False
        self.current_wifi_analysis: Optional[WifiAnalysis] = None
        self.current_moxa_analysis = None

        # Configuration du logging
        self.logger = self._setup_logging()
        # Gestionnaire d'historique
        self.history_manager = HistoryManager()

        # Patterns caractéristiques des logs Moxa
        self.moxa_patterns = cfg.get(
            "moxa_patterns",
            [
                "[WLAN] Roaming from AP",
                "Authentication request",
                "Deauthentication from AP",
                "SNR:",
                "Noise floor:",
                "TransferRingToThread",
                "AUTH-RECEIVE",
                "ASSOC-STATE",
                "WLAN-RECEIVE",
            ],
        )

    def _setup_logging(self) -> logging.Logger:
        """Configure le système de journalisation."""
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

    def start_analysis(self, location_tag: str = "") -> bool:
        """Démarre l'analyse réseau complète pour le tag de localisation fourni."""
        try:
            if not self.wifi_collector.start_collection(location_tag=location_tag):
                self.logger.error("Échec du démarrage de la collecte WiFi")
                return False

            self.is_collecting = True
            self.logger.info("Analyse réseau démarrée")
            return True

        except Exception as e:
            self.logger.error(f"Erreur au démarrage de l'analyse: {e}")
            return False

    def stop_analysis(self) -> None:
        """Arrête l'analyse réseau."""
        try:
            if self.is_collecting:
                samples = self.wifi_collector.stop_collection()
                if samples:
                    self.current_wifi_analysis = self.wifi_analyzer.analyze_samples(samples)
                self.is_collecting = False
                self.logger.info("Analyse réseau arrêtée")
        except Exception as e:
            self.logger.error(f"Erreur à l'arrêt de l'analyse: {e}")

    def analyze_moxa_logs(self, log_content: str) -> dict:
        """Analyse les logs Moxa fournis."""
        try:
            if not self.validate_moxa_log(log_content):
                self.logger.error("Contenu invalide ou ne ressemblant pas à des logs Moxa")
                return {"error": "Le contenu ne semble pas être des logs Moxa valides"}

            preprocessed_logs = self.preprocess_moxa_log(log_content)
            self.logger.info("Logs prétraités avec succès")

            config = self.config_manager.get_config().get("network_analyzer", {})
            default_config = config.get(
                "default_moxa_config",
                {
                    "min_transmission_rate": 6,
                    "max_transmission_power": 20,
                    "rts_threshold": 512,
                    "roaming_mechanism": "signal_strength",
                },
            )

            analysis_results = self.moxa_analyzer.analyze_logs(preprocessed_logs, default_config)

            if analysis_results:
                self.current_moxa_analysis = analysis_results
                self.logger.info("Analyse des logs Moxa terminée avec succès")
                return analysis_results

            self.logger.error("L'analyse n'a pas produit de résultats")
            return {"error": "L'analyse n'a pas produit de résultats"}

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse des logs Moxa: {e}")
            return {"error": str(e)}

    def get_combined_report(self) -> Dict:
        """Génère un rapport combiné des analyses WiFi et Moxa."""
        report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "wifi_analysis": None,
            "moxa_analysis": None,
            "recommendations": []
        }

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

        if self.current_moxa_analysis:
            report["moxa_analysis"] = self.current_moxa_analysis

        if self.current_wifi_analysis and self.current_moxa_analysis:
            report["recommendations"] = self._generate_combined_recommendations()

        return report

    def _generate_combined_recommendations(self) -> List[str]:
        """Génère des recommandations basées sur les deux analyses."""
        recommendations = []

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
                )

        if (self.current_moxa_analysis and
            isinstance(self.current_moxa_analysis, dict) and
            'recommendations' in self.current_moxa_analysis):
            recommendations.extend(self.current_moxa_analysis['recommendations'])

        return recommendations

    def export_data(self, export_dir: str = "exports") -> str:
        """Exporte toutes les données d'analyse."""
        try:
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(export_dir, f"network_analysis_{timestamp}.json")

            report = self.get_combined_report()

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            try:
                self.history_manager.save_report(report)
            except Exception as exc:
                self.logger.warning(f"Impossible d'enregistrer l'historique: {exc}")

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
        log_content = log_content.replace("\r\n", "\n").strip()
        log_content = "\n".join(line for line in log_content.split("\n") if line.strip())
        return log_content

    def start_wifi_collection(self) -> None:
        """Démarre la collecte de données WiFi."""
        if not self.is_collecting:
            self.wifi_collector.start_collection()
            self.is_collecting = True
            self.logger.info("Analyse réseau démarrée")

    def stop_wifi_collection(self) -> None:
        """Arrête la collecte de données WiFi."""
        if self.is_collecting:
            self.wifi_collector.stop_collection()
            self.is_collecting = False
            self.logger.info("Analyse réseau arrêtée")
