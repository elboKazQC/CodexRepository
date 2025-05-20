"""Application entry point.

This module instantiates the different UI views and orchestrates their
interaction. The actual user interface components have been extracted
into ``ui.wifi_view`` and ``ui.moxa_view`` for clarity.
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk
import os
from dotenv import load_dotenv


from network_analyzer import NetworkAnalyzer
from ui.wifi_view import WifiView
from ui.moxa_view import MoxaView
from network_scanner import scan_wifi  # re-exported for tests


load_dotenv()


class NetworkAnalyzerUI:
    """Main window coordinating the WiFi and Moxa views."""

    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("Analyseur R\u00e9seau WiFi & Moxa")
        self.master.state('zoomed')

        self.analyzer = NetworkAnalyzer()

        # Default configuration for the Moxa analyzer
        self.default_config = {
            "min_transmission_rate": 12,
            "max_transmission_power": 20,
            "rts_threshold": 512,
            "fragmentation_threshold": 2346,
            "roaming_mechanism": "snr",
            "roaming_difference": 8,
            "remote_connection_check": True,
            "wmm_enabled": True,
            "turbo_roaming": True,
            "ap_alive_check": True,
        }

        self.config_dir = os.path.join(os.path.dirname(__file__), "config")

        self.create_interface()

    # ------------------------------------------------------------------
    # Interface creation
    # ------------------------------------------------------------------
    def create_interface(self) -> None:
        """Create notebook with WiFi and Moxa tabs."""
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


        self.wifi_view = WifiView(self.notebook, self.analyzer)
        self.notebook.add(self.wifi_view.frame, text="Analyse WiFi")


        self.moxa_view = MoxaView(self.notebook, self.config_dir, self.default_config)
        self.notebook.add(self.moxa_view.frame, text="Analyse Moxa")

        # Expose some attributes for backward compatibility with tests
        self.start_button = self.wifi_view.start_button
        self.stop_button = self.wifi_view.stop_button
        self.scan_button = self.wifi_view.scan_button
        self.export_scan_button = self.wifi_view.export_scan_button
        self.scan_tree = self.wifi_view.scan_tree

    # ------------------------------------------------------------------
    # Delegated methods used by tests or other modules
    # ------------------------------------------------------------------
    def setup_graphs(self) -> None:
        self.wifi_view.setup_graphs()

    def start_collection(self) -> None:
        self.wifi_view.start_collection()

    def stop_collection(self) -> None:
        self.wifi_view.stop_collection()

    def scan_nearby_aps(self) -> None:
        self.wifi_view.scan_nearby_aps()

    def export_scan_results(self) -> None:
        self.wifi_view.export_scan_results()

    def export_data(self) -> None:
        self.wifi_view.export_data()

    # Moxa view delegations
    def analyze_moxa_logs(self) -> None:
        self.moxa_view.analyze_moxa_logs()

    def load_config(self) -> None:
        self.moxa_view.load_config()

    def edit_config(self) -> None:
        self.moxa_view.edit_config()

    # Utility wrappers
    def update_status(self, message: str) -> None:
        self.wifi_view.update_status(message)

    def show_error(self, message: str) -> None:
        self.wifi_view.show_error(message)



def main() -> None:
    """Application entry point."""

    try:
        root = tk.Tk()
        # Instantiate the UI using the theme defined in the configuration
        from bootstrap_ui import BootstrapNetworkAnalyzerUI
        app = BootstrapNetworkAnalyzerUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Erreur fatale: {str(e)}")
        tk.messagebox.showerror("Erreur fatale", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
