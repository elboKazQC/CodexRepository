"""Bootstrap-based UI module for the AuditWifiApp.

This module provides a UI built with ttkbootstrap. It reuses the
NetworkAnalyzerUI logic but initializes the interface with a themed
``Window`` when ttkbootstrap is available. If ttkbootstrap is not
installed, it falls back to standard Tkinter widgets.
"""
from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional, Union, cast

from runner import NetworkAnalyzerUI
from app_config import load_config, save_config

try:
    import ttkbootstrap
    BOOTSTRAP_AVAILABLE = True
except ImportError:  # pragma: no cover - library may be missing
    BOOTSTRAP_AVAILABLE = False
    import tkinter.ttk as ttk


class BootstrapNetworkAnalyzerUI(NetworkAnalyzerUI):
    """UI using ttkbootstrap for improved styling."""

    def __init__(
        self,
        master: Optional[Union[tk.Tk, 'ttkbootstrap.Window']] = None,
        theme: Optional[str] = None,
    ):
        # Load theme from YAML config if not provided
        self._config = load_config()
        if theme is None:
            theme = self._config.get("interface", {}).get("theme", "darkly")

        if master is None:
            if BOOTSTRAP_AVAILABLE:
                self.root = ttkbootstrap.Window(themename=theme)
                master = self.root
            else:  # fallback to classic Tk
                master = tk.Tk()

        self._use_bootstrap = BOOTSTRAP_AVAILABLE
        self._theme = theme

        # Cast master to tk.Tk pour satisfaire le type hint du parent
        super().__init__(cast(tk.Tk, master))

    # ------------------------------------------------------------------
    # Theme handling
    # ------------------------------------------------------------------
    def save_theme(self, theme: str) -> None:
        """Persist the selected theme to the YAML configuration."""
        self._config.setdefault("interface", {})["theme"] = theme
        save_config(self._config)

    def change_theme(self, theme: str) -> None:
        """Apply a new theme at runtime and persist it."""
        if not self._use_bootstrap:
            return
        self._theme = theme
        if hasattr(self, "theme_var"):
            self.theme_var.set(theme)
        self.root.style.theme_use(theme)
        self.setup_style()
        self.save_theme(theme)

    def setup_style(self) -> None:
        """Configure styles for the interface."""
        if self._use_bootstrap:
            # Utiliser le style de bootstrap
            style = ttkbootstrap.Style()

            # Configuration des styles de base
            style.configure("TLabel", font=("Helvetica", 10))
            style.configure("TButton", font=("Helvetica", 10))

            # Styles personnalisés avec ttkbootstrap
            style.configure("primary.TButton",
                          font=("Helvetica", 12),
                          padding=10)

            style.configure("success.TButton",
                          font=("Helvetica", 12),
                          padding=10)

            style.configure("danger.TButton",
                          font=("Helvetica", 12),
                          padding=10)

            # Style pour le bouton d'analyse
            style.configure("info.TButton",
                          font=("Helvetica", 12, "bold"),
                          padding=10)
        else:
            super().setup_style()

    def create_interface(self) -> None:
        """Override pour utiliser les widgets ttkbootstrap."""
        if not self._use_bootstrap:
            super().create_interface()
            return

        # Appeler create_interface parent mais avec les styles bootstrap
        super().create_interface()

        # Ajout d'un menu pour changer de thème
        top_frame = ttkbootstrap.Frame(self.master)
        top_frame.pack(fill=tk.X, pady=2)
        ttkbootstrap.Label(top_frame, text="Thème :").pack(side=tk.LEFT)
        self.theme_var = tk.StringVar(master=self.master, value=self._theme)
        themes = self.root.style.theme_names()
        self.theme_menu = ttkbootstrap.OptionMenu(
            top_frame,
            self.theme_var,
            self._theme,
            *themes,
            command=self.change_theme,
        )
        self.theme_menu.pack(side=tk.LEFT, padx=5)

        # Mettre à jour les styles des boutons existants avec les styles ttkbootstrap
        if hasattr(self, 'start_button') and BOOTSTRAP_AVAILABLE:
            self.start_button.configure(style="success.TButton")
        if hasattr(self, 'stop_button') and BOOTSTRAP_AVAILABLE:
            self.stop_button.configure(style="danger.TButton")
        if hasattr(self, 'analyze_button') and BOOTSTRAP_AVAILABLE:
            self.analyze_button.configure(style="primary.TButton")
        if hasattr(self, 'export_button') and BOOTSTRAP_AVAILABLE:
            self.export_button.configure(style="info.TButton")

def main() -> None:
    """Point d'entrée autonome pour le test de l'interface bootstrap."""
    app = BootstrapNetworkAnalyzerUI()
    app.master.mainloop()

if __name__ == "__main__":
    main()

