from dataclasses import dataclass, asdict
from datetime import datetime
import json
import csv
import os
from typing import List, Dict, Any, Optional, Union, Set
from statistics import mean, stdev

@dataclass
class WifiSample:
    timestamp: str
    ssid: str
    bssid: str
    signal_dbm: int
    signal_percent: int
    channel: int
    frequency: str
    frequency_mhz: int
    band: str
    is_connected: bool
    zone: str = "Non spécifiée"  # Zone de test
    latitude: float = 0.0        # Pour géolocalisation future
    longitude: float = 0.0       # Pour géolocalisation future

@dataclass
class SpeedTest:
    timestamp: str
    download_mbps: float
    upload_mbps: float
    latency_ms: float
    jitter_ms: float
    bssid: str
    server_name: str
    server_location: str

@dataclass
class PingTest:
    timestamp: str
    target: str
    min_ms: float
    max_ms: float
    avg_ms: float
    lost_percent: float
    jitter_ms: float

StatDict = Dict[str, Union[int, float, Dict[str, Any], List[Any]]]

class WifiDataCollector:
    def __init__(self, base_path: str = "logs_moxa") -> None:
        self.base_path = base_path
        self.wifi_samples: List[WifiSample] = []
        self.speed_tests: List[SpeedTest] = []
        self.ping_tests: List[PingTest] = []
        self.current_zone: str = "Non spécifiée"
        os.makedirs(base_path, exist_ok=True)
        
    def add_wifi_sample(self, sample: WifiSample):
        sample.zone = self.current_zone
        self.wifi_samples.append(sample)
        
    def add_speed_test(self, test: SpeedTest):
        self.speed_tests.append(test)
        
    def add_ping_test(self, test: PingTest) -> None:
        self.ping_tests.append(test)
        
    def set_zone(self, zone: str) -> None:
        """Définir la zone actuelle des tests"""
        self.current_zone = zone
          def calculate_statistics(self) -> Dict[str, Dict[str, Union[int, float, Dict[str, Union[int, float]], List[Any]]]]:
        """Calculer les statistiques globales des tests"""
        stats: Dict[str, Dict[str, Union[int, float, Dict[str, Union[int, float]], List[Any]]]] = {
            "zones": {},
            "global": {
                "samples_count": len(self.wifi_samples),
                "unique_aps": len(set(s.bssid for s in self.wifi_samples)),
                "signal_stats": {},
                "speed_stats": {},
                "ping_stats": {}
            }
        }
        
        # Statistiques par zone
        for zone in set(s.zone for s in self.wifi_samples):
            zone_samples = [s for s in self.wifi_samples if s.zone == zone]
            if zone_samples:
                signals = [s.signal_dbm for s in zone_samples]
                stats["zones"][zone] = {
                    "samples_count": len(zone_samples),
                    "signal_min": min(signals),
                    "signal_max": max(signals),
                    "signal_avg": mean(signals),
                    "signal_stdev": stdev(signals) if len(signals) > 1 else 0
                }
        
        # Statistiques globales du signal
        all_signals = [s.signal_dbm for s in self.wifi_samples]
        if all_signals:
            stats["global"]["signal_stats"] = {
                "min": min(all_signals),
                "max": max(all_signals),
                "avg": mean(all_signals),
                "stdev": stdev(all_signals) if len(all_signals) > 1 else 0
            }
        
        # Statistiques des tests de débit
        if self.speed_tests:
            downloads = [t.download_mbps for t in self.speed_tests]
            uploads = [t.upload_mbps for t in self.speed_tests]
            latencies = [t.latency_ms for t in self.speed_tests]
            stats["global"]["speed_stats"] = {
                "download_avg": mean(downloads),
                "upload_avg": mean(uploads),
                "latency_avg": mean(latencies),
                "tests_count": len(self.speed_tests)
            }
        
        # Statistiques des tests de ping
        if self.ping_tests:
            avg_latencies = [t.avg_ms for t in self.ping_tests]
            jitters = [t.jitter_ms for t in self.ping_tests]
            stats["global"]["ping_stats"] = {
                "latency_avg": mean(avg_latencies),
                "jitter_avg": mean(jitters),
                "packet_loss_avg": mean(t.lost_percent for t in self.ping_tests),
                "tests_count": len(self.ping_tests)
            }
        
        return stats
    
    def calculate_score(self) -> Dict[str, float]:
        """Calculer un score pondéré basé sur plusieurs critères"""
        stats = self.calculate_statistics()
        score = {
            "signal_strength": 0.0,  # 30%
            "stability": 0.0,        # 20%
            "coverage": 0.0,         # 15%
            "speed": 0.0,            # 20%
            "latency": 0.0,          # 15%
            "total": 0.0             # Score global
        }
        
        # Score force du signal (30%)
        if "signal_stats" in stats["global"]:
            sig_stats = stats["global"]["signal_stats"]
            # -50 dBm ou plus = 100%, -80 dBm ou moins = 0%
            avg_signal_score = min(100, max(0, (sig_stats["avg"] + 80) * (100/30)))
            score["signal_strength"] = avg_signal_score * 0.3
        
        # Score stabilité (20%)
        if "signal_stats" in stats["global"]:
            sig_stats = stats["global"]["signal_stats"]
            # Moins de 3 dB de variation = 100%, plus de 10 dB = 0%
            stability_score = min(100, max(0, (10 - sig_stats.get("stdev", 10)) * (100/7)))
            score["stability"] = stability_score * 0.2
        
        # Score couverture (15%)
        zone_count = len(stats["zones"])
        coverage_score = min(100, zone_count * 20)  # 5 zones ou plus = 100%
        score["coverage"] = coverage_score * 0.15
        
        # Score débit (20%)
        if "speed_stats" in stats["global"]:
            speed_stats = stats["global"]["speed_stats"]
            # Plus de 50 Mbps = 100%, moins de 10 Mbps = 0%
            speed_score = min(100, max(0, (speed_stats["download_avg"] - 10) * (100/40)))
            score["speed"] = speed_score * 0.2
        
        # Score latence (15%)
        if "ping_stats" in stats["global"]:
            ping_stats = stats["global"]["ping_stats"]
            # Moins de 10ms = 100%, plus de 100ms = 0%
            latency_score = min(100, max(0, (100 - ping_stats["latency_avg"]) * (100/90)))
            score["latency"] = latency_score * 0.15
        
        # Score total
        score["total"] = sum(v for k, v in score.items() if k != "total")
        
        return score
    
    def save_to_json(self) -> str:
        """Sauvegarder les données au format JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.base_path}/wifi_test_{timestamp}.json"
        
        data = {
            "timestamp": timestamp,
            "wifi_samples": [asdict(s) for s in self.wifi_samples],
            "speed_tests": [asdict(s) for s in self.speed_tests],
            "ping_tests": [asdict(s) for s in self.ping_tests],
            "statistics": self.calculate_statistics(),
            "score": self.calculate_score()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def save_to_csv(self) -> str:
        """Sauvegarder les données au format CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.base_path}/wifi_test_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # En-tête
            writer.writerow([
                "Timestamp", "Type", "SSID", "BSSID", "Signal (dBm)", "Signal (%)",
                "Channel", "Frequency", "Zone", "Download (Mbps)", "Upload (Mbps)",
                "Latency (ms)", "Jitter (ms)", "Packet Loss (%)"
            ])
            
            # Échantillons WiFi
            for sample in self.wifi_samples:
                writer.writerow([
                    sample.timestamp, "WiFi", sample.ssid, sample.bssid,
                    sample.signal_dbm, sample.signal_percent, sample.channel,
                    sample.frequency, sample.zone, "", "", "", "", ""
                ])
            
            # Tests de débit
            for test in self.speed_tests:
                writer.writerow([
                    test.timestamp, "Speed", "", test.bssid, "", "",
                    "", "", "", test.download_mbps, test.upload_mbps,
                    test.latency_ms, test.jitter_ms, ""
                ])
            
            # Tests de ping
            for test in self.ping_tests:
                writer.writerow([
                    test.timestamp, "Ping", "", "", "", "",
                    "", "", "", "", "", test.avg_ms,
                    test.jitter_ms, test.lost_percent
                ])
        
        return filename
    
    def collect_data(self):
        """Simule la collecte de données Wi-Fi."""
        from random import randint, choice
        sample = WifiSample(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ssid=f"SSID_{randint(1, 10)}",
            bssid=f"00:11:22:33:44:{randint(10, 99):02d}",
            signal_dbm=randint(-80, -30),
            signal_percent=randint(20, 100),
            channel=randint(1, 11),
            frequency="2.4 GHz",
            frequency_mhz=randint(2400, 2500),
            band="2.4 GHz",
            is_connected=choice([True, False]),
            zone=self.current_zone
        )
        self.add_wifi_sample(sample)
        return sample

    def collect_sample(self) -> WifiSample:
        """Collecte un échantillon de données Wi-Fi"""
        try:
            from subprocess import check_output
            import re
            from datetime import datetime

            # Exécuter netsh pour obtenir les informations Wi-Fi
            output = check_output("netsh wlan show interfaces", shell=True).decode('utf-8', errors='ignore')
            
            # Extraire les informations pertinentes
            ssid = re.search(r"SSID\s+: (.*)", output)
            bssid = re.search(r"BSSID\s+: (.*)", output)
            signal = re.search(r"Signal\s+: (\d+)%", output)
            channel = re.search(r"Canal\s+: (\d+)", output)
            radio_type = re.search(r"Type de radio\s+: (.*)", output)
            
            # Valeurs par défaut
            ssid_val = ssid.group(1) if ssid else "Inconnu"
            bssid_val = bssid.group(1) if bssid else "00:00:00:00:00:00"
            signal_percent = int(signal.group(1)) if signal else 0
            channel_val = int(channel.group(1)) if channel else 0
            radio_type_val = radio_type.group(1) if radio_type else "802.11"
            
            # Convertir le pourcentage de signal en dBm (approximation)
            signal_dbm = -100 + (signal_percent * 0.5) if signal_percent else -100
            
            # Déterminer la fréquence en fonction du canal
            if channel_val > 0:
                if channel_val <= 13:
                    freq_mhz = 2412 + ((channel_val - 1) * 5)
                    band = "2.4 GHz"
                else:
                    freq_mhz = 5170 + ((channel_val - 34) * 5)
                    band = "5 GHz"
            else:
                freq_mhz = 0
                band = "Inconnu"
            
            # Créer et retourner un nouvel échantillon
            sample = WifiSample(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ssid=ssid_val,
                bssid=bssid_val,
                signal_dbm=int(signal_dbm),
                signal_percent=signal_percent,
                channel=channel_val,
                frequency=radio_type_val,
                frequency_mhz=freq_mhz,
                band=band,
                is_connected=bool(ssid),
                zone=getattr(self, 'current_zone', "Non spécifiée")
            )
            
            # Ajouter l'échantillon à la liste
            self.wifi_samples.append(sample)
            return sample
            
        except Exception as e:
            print(f"Erreur lors de la collecte des données Wi-Fi : {str(e)}")
            return None
