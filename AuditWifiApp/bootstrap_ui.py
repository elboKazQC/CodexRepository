"""Bootstrap-based UI module for the AuditWifiApp.

This module provides a UI built with ttkbootstrap. It reuses the
NetworkAnalyzerUI logic but initializes the interface with a themed
``Window`` when ttkbootstrap is available. If ttkbootstrap is not
installed, it falls back to standard Tkinter widgets.
"""
from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import Optional, Union, cast, Any

from runner import NetworkAnalyzerUI
from app_config import load_config, save_config

try:
    import ttkbootstrap
    from ttkbootstrap import Style
    from ttkbootstrap.constants import *
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
        # Liste des thèmes disponibles
        self.available_themes = {
            "Light": ["cosmo", "flatly", "litera", "minty", "lumen", "sandstone"],
            "Dark": ["darkly", "cyborg", "vapor", "solar", "superhero"]
        }

        # Load theme from YAML config if not provided
        self._config = load_config()
        if theme is None:
            theme = self._config.get("interface", {}).get("theme", "darkly")

        # Validate theme
        all_themes = [t for themes in self.available_themes.values() for t in themes]
        if theme not in all_themes:
            theme = "darkly"  # Default theme

        # Initialize Tkinter window with ttkbootstrap
        if master is None:
            if BOOTSTRAP_AVAILABLE:
                master = ttkbootstrap.Window(themename=theme)
            else:  # fallback to classic Tk
                master = tk.Tk()

        # Set up bootstrap related attributes
        self._use_bootstrap = BOOTSTRAP_AVAILABLE
        self._theme = theme
        self.style = None
        if BOOTSTRAP_AVAILABLE:
            self.style = Style(theme=theme)

        # Call parent class constructor
        super().__init__(cast(tk.Tk, master))

        # Initialize theme variable
        self.theme_var = tk.StringVar(value=theme)
        if BOOTSTRAP_AVAILABLE:
            self.theme_var.trace_add("write", self._on_theme_change)    def create_interface(self) -> None:
        """Override to create the interface with bootstrap styles."""
        # Create main interface first
        super().create_interface()

        if not self._use_bootstrap:
            return

        # Add theme selector
        self.create_theme_selector()

        # Apply bootstrap styles
        self.apply_bootstrap_styles()

    def apply_bootstrap_styles(self) -> None:
        """Apply bootstrap styles to widgets."""
        if not self._use_bootstrap or not self.style:
            return

        try:
            # Configure base styles
            self.style.configure("TLabel", font=("Helvetica", 10))
            self.style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
            self.style.configure("Subtitle.TLabel", font=("Helvetica", 12, "bold"))

            # Configurer les styles des boutons avec les couleurs bootstrap
            success_opts = {'foreground': 'white', 'background': '#28a745'}  # Vert
            danger_opts = {'foreground': 'white', 'background': '#dc3545'}   # Rouge
            info_opts = {'foreground': 'white', 'background': '#17a2b8'}     # Bleu clair
            primary_opts = {'foreground': 'white', 'background': '#007bff'}  # Bleu

            self.style.configure('success.TButton', **success_opts)
            self.style.configure('danger.TButton', **danger_opts)
            self.style.configure('info.TButton', **info_opts)
            self.style.configure('primary.TButton', **primary_opts)

            # Map styles to buttons
            btn_styles = {
                'start_button': 'success.TButton',
                'stop_button': 'danger.TButton',
                'scan_button': 'info.TButton',
                'moxa_button': 'primary.TButton'
            }

            # Apply styles to buttons
            for btn_name, style_name in btn_styles.items():
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    if isinstance(btn, ttk.Button):
                        btn.configure(style=style_name)

        except Exception as e:
            print(f"Error applying bootstrap styles: {e}")

    def create_theme_selector(self) -> None:
        """Create theme selector dropdown."""
        if not self._use_bootstrap or not self.style:
            return

        try:
            # Create theme selector frame
            theme_frame = ttk.Frame(self.control_frame)
            theme_frame.pack(side=tk.RIGHT, padx=10, pady=5)

            # Configure theme selector styles
            self.style.configure("ThemeSelector.TLabel",
                               font=("Helvetica", 10),
                               padding=5)
            self.style.configure("ThemeSelector.TCombobox",
                               font=("Helvetica", 10),
                               padding=2)

            # Create and pack theme selector widgets
            ttk.Label(theme_frame,
                     text="Theme:",
                     style="ThemeSelector.TLabel").pack(side=tk.LEFT, padx=5)

            themes = [theme for themes in self.available_themes.values()
                     for theme in themes]
            theme_combo = ttk.Combobox(theme_frame,
                                     values=themes,
                                     textvariable=self.theme_var,
                                     style="ThemeSelector.TCombobox")
            theme_combo.pack(side=tk.LEFT)
            theme_combo.bind('<<ComboboxSelected>>',
                           lambda _: self.change_theme(self.theme_var.get()))

        except Exception as e:
            print(f"Error creating theme selector: {e}")

    def change_theme(self, theme: str) -> None:
        """Change the current theme"""
        if not self._use_bootstrap or not self.style:
            return

        try:
            # Validate theme
            all_themes = [t for themes in self.available_themes.values() for t in themes]
            if theme not in all_themes:
                return

            self._theme = theme
            if BOOTSTRAP_AVAILABLE:
                self.style = Style(theme=theme)
                
            # Save theme preference
            if 'interface' not in self._config:
                self._config['interface'] = {}
            self._config['interface']['theme'] = theme
            save_config(self._config)

        except Exception as e:
            print(f"Error changing theme: {e}")
              def _on_theme_change(self, *args) -> None:
        """Handle theme change events"""
        if self.theme_var and self.theme_var.get():
            self.change_theme(self.theme_var.get())
            
        """Point d'entrée autonome pour le test de l'interface bootstrap."""def main() -> None:
    """Point d'entrée autonome pour le test de l'interface bootstrap."""
    root = ttkbootstrap.Window(themename="darkly") if BOOTSTRAP_AVAILABLE else tk.Tk()
    app = BootstrapNetworkAnalyzerUI(master=root, theme="darkly")
    root.mainloop()

if __name__ == "__main__":
    main()

