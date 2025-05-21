#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time
import logging
"""Gestionnaire de tests WiFi.

Ce module orchestre les sessions de tests WiFi en démarrant et arrêtant la
collecte de données via :class:`WifiDataCollector`. Les mesures sont récupérées
de manière asynchrone dans un thread dédié afin de ne pas bloquer l'interface
utilisateur.
"""

from typing import Callable, List, Optional

from wifi_data_collector import WifiDataCollector
from models.wifi_record import WifiRecord

class WifiTestManager:
    """Orchestre l'exécution d'un test WiFi.

    Le gestionnaire démarre et arrête la collecte via :class:`WifiDataCollector`
    et conserve les enregistrements récupérés. Il peut notifier un consommateur
    externe via un callback à chaque nouvelle mesure.
    """

    def __init__(self, data_collector: WifiDataCollector) -> None:
        """Initialiser le gestionnaire.

        Parameters
        ----------
        data_collector : WifiDataCollector
            Instance responsable de la collecte des mesures WiFi.
        """
        self.data_collector: WifiDataCollector = data_collector
        self.test_running: bool = False  # Unique flag for test state
        self.collected_data: List[WifiRecord] = []
        self.test_thread: Optional[threading.Thread] = None
        self.current_zone: str = "Non spécifiée"
        self.callback: Optional[Callable[[WifiRecord], None]] = None
        self.error_count: int = 0
        self.max_errors: int = 3
        self.logger = logging.getLogger(__name__)
        self.logger.debug("WifiTestManager initialisé")

    def start_wifi_test(self, callback: Optional[Callable[[WifiRecord], None]] = None) -> None:
        """Démarrer la collecte dans un thread séparé.

        Parameters
        ----------
        callback : Callable[[WifiRecord], None], optional
            Fonction exécutée à chaque nouvelle mesure collectée.
        """
        if self.test_running:
            self.logger.info("Un test est déjà en cours")
            return

        self.logger.info("Démarrage du test WiFi")
        self.test_running = True
        self.collected_data = []
        self.callback = callback
        self.error_count = 0

        # Start PowerShell collection in data collector
        if not self.data_collector.start_collection(zone=self.current_zone):
            self.logger.info("Erreur lors du démarrage de la collecte")
            self.test_running = False
            return

        self.test_thread = threading.Thread(target=self._run_test)
        self.test_thread.daemon = True
        self.test_thread.start()
        self.logger.debug("Thread de test démarré")

    def _run_test(self) -> None:
        """Boucle interne de collecte.

        Cette méthode est exécutée dans un thread dédié. Elle récupère
        périodiquement la dernière mesure depuis ``WifiDataCollector`` et la
        stocke dans :attr:`collected_data`. En cas d'erreur répétée la collecte
        est arrêtée automatiquement.
        """
        self.logger.debug("Thread de test WiFi démarré")
        while self.test_running and self.error_count < self.max_errors:
            try:
                # Collecter un échantillon de données
                self.logger.debug("Tentative de collecte d'échantillon...")
                sample = self.data_collector.get_latest_record()
                if sample:
                    self.logger.debug(f"Échantillon collecté : {sample}")
                    self.collected_data.append(sample)
                    if self.callback:
                        try:
                            self.callback(sample)
                            self.logger.debug("Callback exécuté avec succès")
                        except Exception as cb_error:
                            self.logger.debug(f"Erreur dans le callback : {cb_error}")
                    self.error_count = 0  # Réinitialiser le compteur d'erreurs en cas de succès
                else:
                    self.error_count += 1
                    self.logger.debug(
                        f"Échantillon non valide. Tentative {self.error_count}/{self.max_errors}")

                time.sleep(1)  # Réduit à 1 seconde pour une collecte plus fréquente

            except Exception as e:
                self.error_count += 1
                self.logger.debug(
                    f"Erreur lors de la collecte (tentative {self.error_count}/{self.max_errors}): {e}")
                if self.error_count >= self.max_errors:
                    self.logger.info("Trop d'erreurs consécutives, arrêt du test")
                    self.test_running = False
                time.sleep(2)  # Réduit à 2 secondes en cas d'erreur

        self.logger.debug("Thread de test WiFi terminé")

    def stop_wifi_test(self) -> List[WifiRecord]:
        """Arrêter proprement la collecte.

        Returns
        -------
        list[WifiRecord]
            L'ensemble des mesures accumulées pendant le test.
        """
        self.logger.info("Arrêt du test WiFi")
        self.test_running = False

        # Stop PowerShell collection in data collector
        self.data_collector.stop_collection()

        if self.test_thread and self.test_thread.is_alive():
            self.logger.debug("Attente de la fin du thread...")
            self.test_thread.join(timeout=2.0)
        self.logger.info(
            f"Test terminé. {len(self.collected_data)} échantillons collectés")
        return self.collected_data

    def set_zone(self, zone_name: str) -> None:
        """Définir la zone géographique associée au test."""
        self.current_zone = zone_name
        if hasattr(self.data_collector, 'current_zone'):
            self.data_collector.current_zone = zone_name

    def set_location_tag(self, tag: str) -> None:
        """Renseigner un tag permettant d'identifier la localisation précise."""
        if hasattr(self.data_collector, 'current_location_tag'):
            self.data_collector.current_location_tag = tag

    def is_collecting(self) -> bool:
        """Indiquer si un test est en cours."""
        return self.test_running
