#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
import logging

class HistoryManager:
    """Gestionnaire d'historique pour les rapports d'analyse réseau"""

    def __init__(self, history_dir="logs"):
        """Initialise le gestionnaire d'historique

        Args:
            history_dir (str): Répertoire où stocker les rapports d'historique
        """
        self.history_dir = history_dir

        # Crée le répertoire d'historique s'il n'existe pas
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)

        self.logger = logging.getLogger(__name__)

    def save_report(self, report):
        """Enregistre un rapport dans l'historique

        Args:
            report (dict): Le rapport à sauvegarder

        Returns:
            str: Le chemin du fichier où le rapport a été sauvegardé
        """
        try:
            # Génère un nom de fichier unique basé sur la date et l'heure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_report_{timestamp}.json"
            filepath = os.path.join(self.history_dir, filename)

            # Ajoute la date au rapport
            report['timestamp'] = datetime.now().isoformat()

            # Sauvegarde le rapport au format JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4, ensure_ascii=False)

            self.logger.info(f"Rapport sauvegardé: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du rapport: {e}")
            return None

    def get_history(self):
        """Récupère la liste des rapports d'historique

        Returns:
            list: Liste des chemins de fichiers des rapports
        """
        try:
            reports = []
            for filename in os.listdir(self.history_dir):
                if filename.startswith("network_report_") and filename.endswith(".json"):
                    reports.append(os.path.join(self.history_dir, filename))
            return sorted(reports, reverse=True)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return []

    def load_report(self, filepath):
        """Charge un rapport depuis un fichier

        Args:
            filepath (str): Chemin du fichier à charger

        Returns:
            dict: Le contenu du rapport ou None en cas d'erreur
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du rapport {filepath}: {e}")
            return None
