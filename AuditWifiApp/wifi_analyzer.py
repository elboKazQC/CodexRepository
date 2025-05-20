"""
Module d'analyse WiFi pour l'application AuditWifiApp.
Fournit des fonctionnalités d'analyse des données WiFi collectées.
"""

import os
import json
import logging
import subprocess
from datetime import datetime
import statistics
from typing import Dict, List, Optional, Tuple

class WifiAnalyzer:
    def __init__(self):
        self.script_path = os.path.join(os.path.dirname(__file__), 'wifi_monitor.ps1')
        self.is_collecting = False
        self.samples = []
        self.error_count = 0
        self.max_errors = 5
        self.min_signal_strength = -90  # dBm
        self.good_signal_strength = -67  # dBm
        self.setup_logging()

    def setup_logging(self) -> None:
        """Configure le système de journalisation"""
        self.logger = logging.getLogger('WifiAnalyzer')
        self.logger.setLevel(logging.DEBUG)

        # Création du dossier logs s'il n'existe pas
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        # Handler pour fichier détaillé
        detail_handler = logging.FileHandler(os.path.join(log_dir, 'wifi_analysis.log'))
        detail_handler.setLevel(logging.DEBUG)
        detail_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        detail_handler.setFormatter(detail_formatter)

        # Handler pour la console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(detail_handler)
        self.logger.addHandler(console_handler)

    def start_collection(self) -> bool:
        """Démarre la collecte des données WiFi"""
        try:
            if not os.path.exists(self.script_path):
                raise FileNotFoundError(f"Script PowerShell introuvable: {self.script_path}")

            self.logger.info("Démarrage de l'analyse WiFi...")
            self.samples = []
            self.error_count = 0
            self.is_collecting = True
            self.logger.info("Analyse WiFi démarrée avec succès")
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage: {str(e)}")
            return False

    def collect_sample(self) -> Optional[Dict]:
        """Collecte un échantillon de données WiFi"""
        if not self.is_collecting:
            return None

        try:
            self.logger.debug("Collecte d'un nouvel échantillon...")
            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", self.script_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, encoding='latin1')

            if result.returncode != 0:
                self.handle_error(f"Erreur PowerShell: {result.stderr}")
                return None

            try:
                data = json.loads(result.stdout)
                data['timestamp'] = datetime.now().isoformat()
                self.samples.append(data)

                signal = data.get('Signal', 'N/A')
                quality = data.get('SignalQuality', 'N/A')
                ssid = data.get('SSID', 'N/A')

                self.logger.info(f"Échantillon collecté - SSID: {ssid}, Signal: {signal} dBm, Qualité: {quality}%")

                # Analyse en temps réel
                if signal != 'N/A' and float(signal) < self.min_signal_strength:
                    self.logger.warning(f"Signal faible détecté: {signal} dBm")

                return data

            except json.JSONDecodeError as je:
                self.handle_error(f"Erreur de parsing JSON: {str(je)}")
                return None

        except Exception as e:
            self.handle_error(f"Erreur de collecte: {str(e)}")
            return None

    def handle_error(self, error_msg: str) -> None:
        """Gère les erreurs de collecte"""
        self.error_count += 1
        self.logger.error(f"Erreur ({self.error_count}/{self.max_errors}): {error_msg}")

        if self.error_count >= self.max_errors:
            self.logger.critical("Nombre maximum d'erreurs atteint, arrêt de la collecte")
            self.stop_collection()

    def stop_collection(self) -> List[Dict]:
        """Arrête la collecte et retourne les résultats"""
        self.logger.info("Arrêt de la collecte WiFi")
        self.is_collecting = False
        return self.analyze_results()

    def analyze_results(self) -> List[Dict]:
        """Analyse les résultats collectés"""
        if not self.samples:
            self.logger.warning("Aucun échantillon à analyser")
            return []

        try:
            # Extraction des signaux valides
            signals = [float(s['Signal']) for s in self.samples if 'Signal' in s and s['Signal'] != 'N/A']

            if signals:
                avg_signal = statistics.mean(signals)
                min_signal = min(signals)
                max_signal = max(signals)

                # Calcul de la stabilité
                signal_std = statistics.stdev(signals) if len(signals) > 1 else 0
                stability = "Stable" if signal_std < 5 else "Instable"

                # Évaluation de la qualité
                quality = "Bonne" if avg_signal > self.good_signal_strength else \
                         "Moyenne" if avg_signal > self.min_signal_strength else \
                         "Faible"

                analysis = {
                    "nombre_echantillons": len(self.samples),
                    "signal_moyen": round(avg_signal, 2),
                    "signal_min": round(min_signal, 2),
                    "signal_max": round(max_signal, 2),
                    "stabilite": stability,
                    "qualite_generale": quality,
                    "ecart_type": round(signal_std, 2)
                }

                self.logger.info("Analyse terminée :")
                for key, value in analysis.items():
                    self.logger.info(f"{key}: {value}")

                self.samples.append({"analysis": analysis})

            return self.samples

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse: {str(e)}")
            return self.samples

    def get_signal_quality(self, signal: float) -> Tuple[str, str]:
        """Évalue la qualité d'un signal WiFi"""
        if signal > self.good_signal_strength:
            return "Excellent", "#4CAF50"
        elif signal > -70:
            return "Bon", "#8BC34A"
        elif signal > self.min_signal_strength:
            return "Moyen", "#FFC107"
        else:
            return "Faible", "#F44336"
