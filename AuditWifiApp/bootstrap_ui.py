"""Bootstrap-based UI module for the AuditWifiApp.

This module provides a UI built with ttkbootstrap. It reuses the
NetworkAnalyzerUI logic but initializes the interface with a themed
``Window`` when ttkbootstrap is available. If ttkbootstrap is not
installed, it falls back to standard Tkinter widgets.
"""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk  # Add ttk import
from typing import Optional, Union, cast

from runner import NetworkAnalyzerUI
from app_config import load_config, save_config

try:
    import ttkbootstrap
    from ttkbootstrap.constants import *
    from ttkbootstrap.style import Bootstyle
    BOOTSTRAP_AVAILABLE = True
except ImportError:  # pragma: no cover - library may be missing
    BOOTSTRAP_AVAILABLE = False


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
        self._theme = theme if theme is not None else "darkly"

        # Initialize theme variable for dynamic theme switching
        if BOOTSTRAP_AVAILABLE:
            self.theme_var = tk.StringVar(value=self._theme)
            self.theme_var.trace_add("write", lambda *args: self.change_theme(self.theme_var.get()))

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
            # Définir les styles avec ttkbootstrap
            style = ttkbootstrap.Style()

            # Style des labels
            style.configure("TLabel", font=("Helvetica", 10))
            style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))

            # Style des boutons
            style.configure("primary.TButton",
                          font=("Helvetica", 11),
                          padding=5)

            style.configure("success.TButton",
                          font=("Helvetica", 11),
                          padding=5)

            style.configure("danger.TButton",
                          font=("Helvetica", 11),
                          padding=5)

            style.configure("info.TButton",
                          font=("Helvetica", 11, "bold"),
                          padding=5)

            # Style des frames
            style.configure("TFrame", padding=2)
            style.configure("TLabelframe", padding=5)

            # Style du Notebook
            style.configure("TNotebook", padding=2)
            style.configure("TNotebook.Tab", padding=(10, 2))

            # Style pour les zones de texte
            if "dark" in self._theme.lower():
                bg_color = "#2f2f2f"
                fg_color = "#ffffff"
                select_bg = "#007bff"

                widget_names = ["stats_text", "wifi_alert_text",
                              "moxa_input", "moxa_config_text",
                              "moxa_params_text", "moxa_results"]

                for widget_name in widget_names:
                    widget = getattr(self, widget_name, None)
                    if widget is not None:
                        widget.configure(
                            background=bg_color,
                            foreground=fg_color,
                            insertbackground=fg_color,
                            selectbackground=select_bg
                        )

        else:
            super().setup_style()

    def create_interface(self) -> None:
        """Override pour utiliser les widgets ttkbootstrap."""
        if not self._use_bootstrap:
            super().create_interface()
            return

        # Buttons styles mapping
        button_styles = {
            'start_button': 'success.TButton',
            'stop_button': 'danger.TButton',
            'scan_button': 'info.TButton',
            'export_scan_button': 'primary.TButton',
            'analyze_button': 'primary.TButton',
            'export_button': 'info.TButton'
        }

        # Créer l'interface de base
        super().create_interface()

        # Mettre à jour les styles des boutons
        for btn_name, style_name in button_styles.items():
            if hasattr(self, btn_name):
                btn = getattr(self, btn_name)
                if isinstance(btn, (ttk.Button, ttkbootstrap.Button)):
                    btn.configure(style=style_name)

def main() -> None:
    """Point d'entrée autonome pour le test de l'interface bootstrap."""
    app = BootstrapNetworkAnalyzerUI()
    app.master.mainloop()

if __name__ == "__main__":
    main()

