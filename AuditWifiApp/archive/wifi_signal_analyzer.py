#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import requests
from datetime import datetime

class WifiAnalyzer:
    """
    Analyse les données WiFi collectées et fournit des recommandations basées sur les métriques de signal,
    les performances de roaming, et d'autres indicateurs de qualité réseau.
    """

    def __init__(self, api_key=None):
        """
        Initialise l'analyseur WiFi avec les paramètres nécessaires.
        
        Args:
            api_key (str, optional): Clé API pour OpenAI. Si non fournie, tente de la récupérer
                                    depuis les variables d'environnement.
        """
        self.api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4"
        self.max_tokens = 1500
        
        # Métriques de référence pour les zones à risque
        self.risk_thresholds = {
            "signal_strength_dbm": -70,  # Signal en dBm en dessous duquel on considère une zone à risque
            "signal_strength_percent": 40,  # Signal en pourcentage en dessous duquel on considère une zone à risque
            "ping_ms": 50,  # Ping en ms au-dessus duquel on considère une zone à risque
            "packet_loss_percent": 2  # Perte de paquets en pourcentage au-dessus duquel on considère une zone à risque
        }

    def analyze_wifi_data(self, wifi_logs):
        """
        Analyse les données WiFi avec l'API OpenAI pour générer des recommandations.
        
        Args:
            wifi_logs (str): Contenu des logs WiFi à analyser
            
        Returns:
            str: Résultat de l'analyse sous forme de texte brut
            
        Raises:
            ValueError: Si aucune clé API n'est fournie
            RuntimeError: Si l'API renvoie une erreur
        """
        if not self.api_key:
            raise ValueError("Clé API OpenAI non configurée. Veuillez la définir dans les variables d'environnement.")
        
        # Nettoyer et formater les logs
        clean_logs = wifi_logs.replace("\r\n", "\n").strip()
        
        # Créer le prompt pour l'API
        prompt = (
            "En tant qu'expert Wi-Fi, analyser ces logs de test réseau provenant d'un PC portable. "
            "Les logs incluent les changements d'AP (roaming) et des tests de débit.\n\n"
            "INSTRUCTIONS IMPORTANTES:\n"
            "1. Analyser la stabilité du signal, la qualité du roaming, et la performance réseau\n"
            "2. Évaluer si le réseau est adapté pour une flotte d'AMR (robots mobiles)\n"
            "3. RÉPONDRE EN FORMAT TEXTE SIMPLE, mais structuré avec des titres clairs pour:\n"
            "   - Évaluation globale du réseau\n"
            "   - Qualité du signal (min/max dBm, stabilité)\n"
            "   - Performance du roaming (temps moyen, réussites/échecs)\n"
            "   - Problèmes identifiés\n"
            "   - Recommandations\n\n"
            f"LOGS À ANALYSER:\n{clean_logs}"
        )
        
        try:
            # Envoyer la requête à l'API OpenAI
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
            
            # Vérifier et retourner la réponse
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                error_msg = f"Erreur API: {response.status_code} - {response.text}"
                self._log_error(error_msg)
                raise RuntimeError(error_msg)
                
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse WiFi: {str(e)}"
            self._log_error(error_msg)
            raise RuntimeError(error_msg)
    
    def identify_risk_zones(self, wifi_data):
        """
        Identifie les zones à risque basées sur les données WiFi collectées.
        
        Args:
            wifi_data (list): Liste d'échantillons WiFi avec leurs métriques
            
        Returns:
            list: Liste des zones à risque avec les métriques problématiques
        """
        risk_zones = []
        
        for sample in wifi_data:
            risks = []
            
            # Vérifier le signal
            if hasattr(sample, 'signal_dbm') and sample.signal_dbm < self.risk_thresholds["signal_strength_dbm"]:
                risks.append(f"Signal faible: {sample.signal_dbm} dBm")
                
            if hasattr(sample, 'signal_percent') and sample.signal_percent < self.risk_thresholds["signal_strength_percent"]:
                risks.append(f"Signal faible: {sample.signal_percent}%")
            
            # Vérifier le ping si disponible
            if hasattr(sample, 'ping_ms') and sample.ping_ms > self.risk_thresholds["ping_ms"]:
                risks.append(f"Latence élevée: {sample.ping_ms} ms")
            
            # Si des risques sont identifiés, ajouter la zone à la liste
            if risks and hasattr(sample, 'zone'):
                risk_zones.append({
                    "zone": sample.zone,
                    "timestamp": sample.timestamp if hasattr(sample, 'timestamp') else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "risks": risks,
                    "sample": sample
                })
        
        return risk_zones
    
    def _log_error(self, error_message):
        """
        Enregistre les erreurs dans un fichier de journal.
        
        Args:
            error_message (str): Message d'erreur à enregistrer
        """
        try:
            with open("api_errors.log", "a") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp} - WIFI_ANALYZER - {error_message}\n")
        except:
            # Si l'enregistrement échoue, ne pas bloquer l'exécution
            pass
