class WifiAnalyzer:
    """
    Analyse les données WiFi collectées et fournit des recommandations basées sur les métriques de signal,
    les performances et les indicateurs de qualité réseau.
    """
    def __init__(self):
        self.thresholds = {
            "signal_strength": {
                "excellent": -50,
                "good": -60,
                "fair": -70,
                "poor": -80
            },
            "ping_ms": 50,  # Ping en ms au-dessus duquel on considère une zone à risque
            "packet_loss_percent": 2  # Perte de paquets en pourcentage au-dessus duquel on considère une zone à risque
        }

    def analyze(self, wifi_data):
        """
        Analyse les données WiFi et fournit un rapport détaillé.

        Args:
            wifi_data: Dictionnaire contenant les données WiFi collectées

        Returns:
            dict: Résultats de l'analyse avec recommandations
        """
        try:
            results = {
                "status": "ok",
                "metrics": self._analyze_metrics(wifi_data),
                "recommendations": self._generate_recommendations(wifi_data)
            }
            return results

        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de l'analyse WiFi: {str(e)}"
            }

    def _analyze_metrics(self, wifi_data):
        """Analyse les métriques WiFi principales."""
        metrics = {
            "signal_quality": self._evaluate_signal_quality(wifi_data.get("rssi", 0)),
            "connection_stability": self._evaluate_connection_stability(
                wifi_data.get("packet_loss", 0),
                wifi_data.get("ping", 0)
            ),
            "statistics": {
                "avg_signal": wifi_data.get("rssi", 0),
                "avg_ping": wifi_data.get("ping", 0),
                "packet_loss": wifi_data.get("packet_loss", 0)
            }
        }
        return metrics

    def _evaluate_signal_quality(self, rssi):
        """Évalue la qualité du signal basée sur le RSSI."""
        if rssi >= self.thresholds["signal_strength"]["excellent"]:
            return "Excellent"
        elif rssi >= self.thresholds["signal_strength"]["good"]:
            return "Bon"
        elif rssi >= self.thresholds["signal_strength"]["fair"]:
            return "Faible"
        else:
            return "Critique"

    def _evaluate_connection_stability(self, packet_loss, ping):
        """Évalue la stabilité de la connexion."""
        if (packet_loss <= self.thresholds["packet_loss_percent"] and
            ping <= self.thresholds["ping_ms"]):
            return "Stable"
        elif packet_loss > self.thresholds["packet_loss_percent"] * 2 or ping > self.thresholds["ping_ms"] * 2:
            return "Instable"
        else:
            return "Dégradée"

    def _generate_recommendations(self, wifi_data):
        """Génère des recommandations basées sur l'analyse."""
        recommendations = []
        rssi = wifi_data.get("rssi", 0)
        ping = wifi_data.get("ping", 0)
        packet_loss = wifi_data.get("packet_loss", 0)

        # Recommendations basées sur le signal
        if rssi < self.thresholds["signal_strength"]["fair"]:
            recommendations.append({
                "type": "signal",
                "severity": "high" if rssi < self.thresholds["signal_strength"]["poor"] else "medium",
                "message": "Signal WiFi faible détecté. Actions recommandées:",
                "actions": [
                    "Rapprochez-vous du point d'accès",
                    "Vérifiez les obstacles physiques",
                    "Envisagez l'ajout d'un point d'accès supplémentaire"
                ]
            })

        # Recommendations basées sur la stabilité
        if ping > self.thresholds["ping_ms"] or packet_loss > self.thresholds["packet_loss_percent"]:
            recommendations.append({
                "type": "stability",
                "severity": "high" if packet_loss > self.thresholds["packet_loss_percent"] * 2 else "medium",
                "message": "Problèmes de stabilité détectés. Actions recommandées:",
                "actions": [
                    "Vérifiez les interférences WiFi",
                    "Optimisez la configuration du point d'accès",
                    "Considérez un changement de canal WiFi"
                ]
            })

        return recommendations
