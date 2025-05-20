import numpy as np
from typing import List, Tuple, Dict
from datetime import datetime
from dataclasses import dataclass
from .wifi_collector import WifiSample

@dataclass
class WifiAnalysis:
    average_signal: float
    min_signal: float
    max_signal: float
    signal_stability: float
    connection_quality: float
    dropout_count: int
    timestamps: List[str]
    signal_values: List[float]
    quality_values: List[float]

class WifiAnalyzer:
    def __init__(self):
        self.signal_threshold = -70  # dBm
        self.quality_threshold = 40  # %
        self.stability_window = 10  # échantillons

    def analyze_samples(self, samples: List[WifiSample]) -> WifiAnalysis:
        """Analyse une liste d'échantillons WiFi"""
        if not samples:
            return self._create_empty_analysis()

        # Extraction des données
        timestamps = [s.timestamp for s in samples]
        signals = [s.signal_strength for s in samples]
        qualities = [s.quality for s in samples]

        # Calcul des statistiques de signal
        avg_signal = np.mean(signals)
        min_signal = np.min(signals)
        max_signal = np.max(signals)

        # Calcul de la stabilité du signal
        if len(signals) >= self.stability_window:
            signal_variations = np.abs(np.diff(signals[-self.stability_window:]))
            stability = 100 * (1 - np.mean(signal_variations) / 30)  # 30dBm comme variation max
            stability = max(0, min(100, stability))  # Limiter entre 0 et 100%
        else:
            stability = 0

        # Calcul de la qualité de connexion globale
        connection_quality = np.mean(qualities)

        # Détection des déconnexions (signal < threshold)
        dropouts = sum(1 for s in signals if s < self.signal_threshold)

        return WifiAnalysis(
            average_signal=round(avg_signal, 1),
            min_signal=round(min_signal, 1),
            max_signal=round(max_signal, 1),
            signal_stability=round(stability, 1),
            connection_quality=round(connection_quality, 1),
            dropout_count=dropouts,
            timestamps=timestamps,
            signal_values=signals,
            quality_values=qualities
        )

    def _create_empty_analysis(self) -> WifiAnalysis:
        """Crée une analyse vide"""
        return WifiAnalysis(
            average_signal=0.0,
            min_signal=0.0,
            max_signal=0.0,
            signal_stability=0.0,
            connection_quality=0.0,
            dropout_count=0,
            timestamps=[],
            signal_values=[],
            quality_values=[]
        )

    def _calculate_stability(self, signals: List[float]) -> float:
        """Calcule la stabilité du signal"""
        if len(signals) < self.stability_window:
            return np.std(signals) if signals else 0.0

        # Calcul de l'écart-type mobile
        stdev = np.std(signals[-self.stability_window:])
        # Normalisation entre 0 et 100
        stability = 100 * (1 - min(stdev / 20, 1))  # 20 dBm comme variation max
        return stability

    def _evaluate_connection_quality(
        self,
        signals: List[float],
        qualities: List[float]
    ) -> float:
        """Évalue la qualité globale de la connexion"""
        if not signals or not qualities:
            return 0.0

        # Poids des différents facteurs
        signal_weight = 0.4
        quality_weight = 0.3
        stability_weight = 0.3

        # Score basé sur le signal
        avg_signal = np.mean(signals)
        signal_score = 100 * (1 - abs(min(avg_signal, -30) + 30) / 60)

        # Score basé sur la qualité
        quality_score = np.mean(qualities)

        # Score basé sur la stabilité
        stability_score = self._calculate_stability(signals)

        # Score final pondéré
        final_score = (
            signal_weight * signal_score +
            quality_weight * quality_score +
            stability_weight * stability_score
        )

        return min(max(final_score, 0), 100)

    def _count_dropouts(self, signals: List[float]) -> int:
        """Compte le nombre de déconnexions"""
        if not signals:
            return 0

        dropouts = 0
        for i in range(1, len(signals)):
            if (signals[i] < self.signal_threshold and
                signals[i-1] >= self.signal_threshold):
                dropouts += 1

        return dropouts

    def get_signal_trends(
        self,
        samples: List[WifiSample]
    ) -> Tuple[List[str], List[float]]:
        """Extrait les tendances du signal"""
        if not samples:
            return [], []

        timestamps = [s.timestamp for s in samples]
        signals = [float(s.signal_strength) for s in samples]

        return timestamps, signals

    def get_quality_distribution(self, samples: List[WifiSample]) -> Dict[str, int]:
        """Analyse la distribution de la qualité du signal"""
        if not samples:
            return {}

        # Définition des plages de qualité
        ranges = {
            "Excellent": (80, 100),
            "Bon": (60, 80),
            "Moyen": (40, 60),
            "Faible": (20, 40),
            "Mauvais": (0, 20)
        }

        # Comptage des échantillons dans chaque plage
        distribution = {range_name: 0 for range_name in ranges}

        for sample in samples:
            quality = sample.quality
            for range_name, (min_val, max_val) in ranges.items():
                if min_val <= quality < max_val:
                    distribution[range_name] += 1
                    break

        return distribution
