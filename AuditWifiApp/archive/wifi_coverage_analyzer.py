#!/usr/bin/env python
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt

class WifiCoverageAnalyzer:
    """
    Analyseur spécialisé dans l'évaluation de la couverture WiFi à partir des données collectées
    lors des déplacements sur site. Permet de générer des cartes de couverture, d'identifier
    les zones à risque et de proposer des optimisations pour améliorer la couverture globale.
    """

    def __init__(self):
        """
        Initialise l'analyseur de couverture WiFi.
        """
        self.coverage_data = []
        self.risk_zones = []
    
    def analyze_coverage(self, samples, map_dimensions=None):
        """
        Analyse les données de couverture WiFi à partir des échantillons collectés.
        
        Args:
            samples (list): Liste d'échantillons WiFi avec position (x, y) et signal strength (RSSI)
            map_dimensions (tuple): Dimensions (largeur, hauteur) de la carte en mètres (optionnel)
            
        Returns:
            dict: Résultat de l'analyse de couverture
        """
        if not samples:
            return {
                "status": "error",
                "message": "Aucun échantillon à analyser"
            }
        
        # Stocker les données de couverture
        self.coverage_data = samples
        
        # Identifier les zones à risque (RSSI < -70 dBm)
        self.risk_zones = [
            sample for sample in samples
            if sample.get("rssi", 0) < -70
        ]
        
        # Calculer les métriques générales
        avg_rssi = sum(sample.get("rssi", 0) for sample in samples) / len(samples) if samples else 0
        min_rssi = min((sample.get("rssi", 0) for sample in samples), default=0)
        max_rssi = max((sample.get("rssi", 0) for sample in samples), default=0)
        
        # Calculer la couverture par zone si les dimensions sont fournies
        zone_coverage = {}
        if map_dimensions:
            zone_coverage = self._calculate_zone_coverage(samples, map_dimensions)
        
        return {
            "status": "success",
            "coverage_stats": {
                "average_rssi": round(avg_rssi, 2),
                "min_rssi": min_rssi,
                "max_rssi": max_rssi,
                "sample_count": len(samples),
                "risk_zone_count": len(self.risk_zones),
                "risk_zone_percentage": round(len(self.risk_zones) * 100 / len(samples), 2) if samples else 0
            },
            "zone_coverage": zone_coverage,
            "recommendations": self._generate_coverage_recommendations()
        }
    
    def _calculate_zone_coverage(self, samples, map_dimensions):
        """
        Calcule la couverture WiFi par zone en divisant la carte en grille.
        
        Args:
            samples (list): Liste d'échantillons WiFi
            map_dimensions (tuple): Dimensions (largeur, hauteur) de la carte en mètres
            
        Returns:
            dict: Couverture par zone
        """
        width, height = map_dimensions
        
        # Diviser la carte en grille 3x3
        grid_width = width / 3
        grid_height = height / 3
        
        zones = {}
        
        # Classifier chaque échantillon dans une zone
        for sample in samples:
            x = sample.get("x", 0)
            y = sample.get("y", 0)
            rssi = sample.get("rssi", 0)
            
            zone_x = int(x / grid_width)
            zone_y = int(y / grid_height)
            
            zone_id = f"zone_{zone_x}_{zone_y}"
            
            if zone_id not in zones:
                zones[zone_id] = {
                    "samples": [],
                    "avg_rssi": 0,
                    "risk_samples": 0
                }
            
            zones[zone_id]["samples"].append(rssi)
            if rssi < -70:
                zones[zone_id]["risk_samples"] += 1
        
        # Calculer les statistiques par zone
        for zone_id, zone_data in zones.items():
            samples = zone_data["samples"]
            zone_data["avg_rssi"] = sum(samples) / len(samples) if samples else 0
            zone_data["sample_count"] = len(samples)
            zone_data["risk_percentage"] = round(zone_data["risk_samples"] * 100 / len(samples), 2) if samples else 0
        
        return zones
    
    def _generate_coverage_recommendations(self):
        """
        Génère des recommandations pour améliorer la couverture WiFi.
        
        Returns:
            list: Liste de recommandations
        """
        recommendations = []
        
        # Analyser les zones à risque
        if len(self.risk_zones) > 0:
            risk_percentage = len(self.risk_zones) * 100 / len(self.coverage_data) if self.coverage_data else 0
            
            if risk_percentage > 30:
                recommendations.append({
                    "priority": "Haute",
                    "problem": "Couverture WiFi insuffisante dans plus de 30% des zones",
                    "solution": "Installer des points d'accès supplémentaires dans les zones à risque identifiées"
                })
            elif risk_percentage > 10:
                recommendations.append({
                    "priority": "Moyenne",
                    "problem": "Couverture WiFi faible dans certaines zones",
                    "solution": "Repositionner les points d'accès existants pour une meilleure couverture"
                })
            else:
                recommendations.append({
                    "priority": "Basse",
                    "problem": "Quelques points isolés avec signal faible",
                    "solution": "Optimiser la puissance de transmission des points d'accès existants"
                })
        
        # Ajouter des recommandations générales
        if len(self.coverage_data) > 0:
            avg_rssi = sum(sample.get("rssi", 0) for sample in self.coverage_data) / len(self.coverage_data)
            
            if avg_rssi < -65:
                recommendations.append({
                    "priority": "Moyenne",
                    "problem": "Signal WiFi moyen faible dans l'ensemble",
                    "solution": "Évaluer les obstacles ou sources d'interférence dans l'environnement"
                })
        
        return recommendations
    
    def generate_coverage_map(self, output_file="coverage_map.png", show_risk_zones=True):
        """
        Génère une carte de couverture WiFi à partir des données collectées.
        
        Args:
            output_file (str): Chemin du fichier de sortie
            show_risk_zones (bool): Indique si les zones à risque doivent être mises en évidence
            
        Returns:
            str: Chemin du fichier généré ou message d'erreur
        """
        if not self.coverage_data:
            return "Erreur: Aucune donnée de couverture disponible"
        
        try:
            # Extraire les coordonnées et les valeurs RSSI
            x = [sample.get("x", 0) for sample in self.coverage_data]
            y = [sample.get("y", 0) for sample in self.coverage_data]
            rssi = [sample.get("rssi", 0) for sample in self.coverage_data]
            
            # Créer la figure
            plt.figure(figsize=(10, 8))
            
            # Créer la carte de couverture (color mesh)
            plt.scatter(x, y, c=rssi, cmap='RdYlGn_r', alpha=0.8, s=30)
            plt.colorbar(label='RSSI (dBm)')
            
            # Mettre en évidence les zones à risque
            if show_risk_zones and self.risk_zones:
                risk_x = [sample.get("x", 0) for sample in self.risk_zones]
                risk_y = [sample.get("y", 0) for sample in self.risk_zones]
                plt.scatter(risk_x, risk_y, c='red', marker='x', s=50, label='Zones à risque')
                plt.legend()
            
            plt.title('Carte de Couverture WiFi')
            plt.xlabel('X (m)')
            plt.ylabel('Y (m)')
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Sauvegarder la figure
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return output_file
        
        except Exception as e:
            return f"Erreur lors de la génération de la carte: {str(e)}"
