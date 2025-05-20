import numpy as np
from typing import List, Tuple, Dict, Optional
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
        # Seuils supplémentaires utilisés par les autres analyseurs
        self.thresholds = {
            "signal_strength": {
                "excellent": -50,
                "good": -60,
                "fair": -70,
                "poor": -80,
            },
            "ping_ms": 50,
            "packet_loss_percent": 2,
            "snr_db": {
                "excellent": 25,
                "good": 15,
                "fair": 10,
                "poor": 0,
            },
        }

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

    # ------------------------------------------------------------------
    # Logic merged from the previous wifi_signal_analyzer implementation

    def analyze_wifi_data(self, wifi_data: Dict) -> Dict:
        """Analyse un dictionnaire de mesures WiFi simple."""
        try:
            results = {
                "status": "ok",
                "metrics": self._analyze_metrics(wifi_data),
                "recommendations": self._generate_recommendations(wifi_data),
            }
            return results
        except Exception as e:
            return {"status": "error", "message": f"Erreur lors de l'analyse WiFi: {str(e)}"}

    def _analyze_metrics(self, wifi_data: Dict) -> Dict:
        """Analyse les métriques WiFi principales."""
        return {
            "signal_quality": self._evaluate_signal_quality(wifi_data.get("rssi", 0)),
            "snr_quality": self._evaluate_snr(wifi_data.get("snr")),
            "connection_stability": self._evaluate_connection_stability(
                wifi_data.get("packet_loss", 0),
                wifi_data.get("ping", 0),
            ),
            "statistics": {
                "avg_signal": wifi_data.get("rssi", 0),
                "avg_ping": wifi_data.get("ping", 0),
                "packet_loss": wifi_data.get("packet_loss", 0),
            },
        }

    def _evaluate_snr(self, snr: Optional[int]) -> str:
        """Évalue la qualité du SNR."""
        if snr is None:
            return "Inconnu"
        if snr >= self.thresholds["snr_db"]["excellent"]:
            return "Excellent"
        elif snr >= self.thresholds["snr_db"]["good"]:
            return "Bon"
        elif snr >= self.thresholds["snr_db"]["fair"]:
            return "Moyen"
        else:
            return "Faible"

    def _evaluate_signal_quality(self, rssi: float) -> str:
        """Évalue la qualité du signal basée sur le RSSI."""
        if rssi >= self.thresholds["signal_strength"]["excellent"]:
            return "Excellent"
        elif rssi >= self.thresholds["signal_strength"]["good"]:
            return "Bon"
        elif rssi >= self.thresholds["signal_strength"]["fair"]:
            return "Faible"
        else:
            return "Critique"

    def _evaluate_connection_stability(self, packet_loss: float, ping: float) -> str:
        """Évalue la stabilité de la connexion."""
        if packet_loss <= self.thresholds["packet_loss_percent"] and ping <= self.thresholds["ping_ms"]:
            return "Stable"
        elif packet_loss > self.thresholds["packet_loss_percent"] * 2 or ping > self.thresholds["ping_ms"] * 2:
            return "Instable"
        else:
            return "Dégradée"

    def _generate_recommendations(self, wifi_data: Dict) -> List[Dict]:
        """Génère des recommandations basées sur l'analyse des données."""
        recommendations = []
        rssi = wifi_data.get("rssi", 0)
        ping = wifi_data.get("ping", 0)
        packet_loss = wifi_data.get("packet_loss", 0)

        if rssi < self.thresholds["signal_strength"]["fair"]:
            recommendations.append({
                "type": "signal",
                "severity": "high" if rssi < self.thresholds["signal_strength"]["poor"] else "medium",
                "message": "Signal WiFi faible détecté. Actions recommandées:",
                "actions": [
                    "Rapprochez-vous du point d'accès",
                    "Vérifiez les obstacles physiques",
                    "Envisagez l'ajout d'un point d'accès supplémentaire",
                ],
            })

        if ping > self.thresholds["ping_ms"] or packet_loss > self.thresholds["packet_loss_percent"]:
            recommendations.append({
                "type": "stability",
                "severity": "high" if packet_loss > self.thresholds["packet_loss_percent"] * 2 else "medium",
                "message": "Problèmes de stabilité détectés. Actions recommandées:",
                "actions": [
                    "Vérifiez les interférences WiFi",
                    "Optimisez la configuration du point d'accès",
                    "Considérez un changement de canal WiFi",
                ],
            })

        return recommendations

    # ------------------------------------------------------------------
    # Logic merged from WifiLogAnalyzer for basic log inspection

    def analyze_logs(self, log_data: str) -> Dict:
        """Analyse des logs WiFi génériques."""
        try:
            metrics = self._extract_log_metrics(log_data)
            return {
                "status": "success",
                "metrics": metrics,
                "issues": self._identify_log_issues(metrics),
                "recommendations": self._generate_log_recommendations(metrics),
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur lors de l'analyse: {str(e)}"}

    def _extract_log_metrics(self, log_data: str) -> Dict:
        """Extrait quelques métriques simples des logs WiFi."""
        return {
            "signal_strength": self._log_analyze_signal_strength(log_data),
            "connection_stability": self._log_analyze_stability(log_data),
            "performance_metrics": self._log_analyze_performance(log_data),
        }

    def _log_analyze_signal_strength(self, log_data: str) -> Dict:
        """Analyse la force du signal dans les logs (implémentation simplifiée)."""
        return {"average": -65, "min": -75, "max": -55}

    def _log_analyze_stability(self, log_data: str) -> Dict:
        """Analyse la stabilité de la connexion dans les logs (exemple)."""
        return {"disconnections": 1, "reconnection_time_avg": 2.5}

    def _log_analyze_performance(self, log_data: str) -> Dict:
        """Analyse les performances réseau dans les logs (exemple)."""
        return {"latency_avg": 45, "packet_loss": 0.5}

    def _identify_log_issues(self, metrics: Dict) -> List[str]:
        """Identifie des problèmes potentiels à partir des métriques."""
        issues = []
        if metrics["signal_strength"]["average"] < self.thresholds["signal_strength"]["fair"]:
            issues.append("Signal moyen inférieur au seuil acceptable")
        if metrics["performance_metrics"]["packet_loss"] > self.thresholds["packet_loss_percent"]:
            issues.append("Taux de perte de paquets élevé")
        return issues

    def _generate_log_recommendations(self, metrics: Dict) -> List[str]:
        """Génère des recommandations à partir des métriques de log."""
        recos = []
        if metrics["signal_strength"]["average"] < self.thresholds["signal_strength"]["fair"]:
            recos.append("Améliorer la couverture WiFi ou repositionner l'antenne")
        if metrics["performance_metrics"]["packet_loss"] > self.thresholds["packet_loss_percent"]:
            recos.append("Vérifier les interférences et la qualité du lien")
        return recos
