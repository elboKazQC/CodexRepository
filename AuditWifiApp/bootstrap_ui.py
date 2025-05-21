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
from typing import Optional, Union, cast

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
            "Dark": ["darkly", "cyborg", "vapor", "solar", "superhero", "noovelia"]
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

        # Initialize attributes needed by create_interface
        self._use_bootstrap = BOOTSTRAP_AVAILABLE
        self._theme = theme

        if self._use_bootstrap:
            self.style = Style(theme=theme)
        else:
            self.style = None

        # Now initialize parent class which will call create_interface
        super().__init__(master)

        # Initialize theme variable after parent class initialization
        self.theme_var = tk.StringVar(master=self.master, value=theme)
        if BOOTSTRAP_AVAILABLE:
            self.style = Style(theme=theme)

        # Setup theme handling after parent initialization
        if BOOTSTRAP_AVAILABLE:
            self.theme_var.trace_add("write", self._on_theme_change)

    def create_interface(self) -> None:
        """Override to create the interface with bootstrap styles."""
        if not self._use_bootstrap:
            super().create_interface()
            return

        # Create theme selector first
        self.create_theme_selector()

        # Create main interface
        super().create_interface()

        # Apply bootstrap styles
        self.apply_bootstrap_styles()

    def change_theme(self, theme: str) -> None:
        """Change the current theme"""
        if not self._use_bootstrap or not BOOTSTRAP_AVAILABLE:
            return

        try:
            # Validate theme
            all_themes = [t for themes in self.available_themes.values() for t in themes]
            if theme not in all_themes:
                return

            self._theme = theme

            # Create new style with the selected theme
            self.style = Style(theme=theme)

            # Apply styles to widgets
            self.apply_bootstrap_styles()

            # Save theme to config
            self._config.setdefault("interface", {})["theme"] = theme
            save_config(self._config)

            # Update theme category label
            self._update_theme_category()

        except Exception as e:
            print(f"Error changing theme: {e}")

    def apply_bootstrap_styles(self) -> None:
        """Apply bootstrap styles to widgets"""
        if not self._use_bootstrap or not BOOTSTRAP_AVAILABLE:
            return

        try:
            # Configure base styles
            self.style.configure("TLabel", font=("Helvetica", 10))
            self.style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
            self.style.configure("Subtitle.TLabel", font=("Helvetica", 12, "bold"))
            self.style.configure("Alert.TLabel", font=("Helvetica", 12))
            self.style.configure("info.TLabel")

            # Configurer les styles des boutons avec les couleurs bootstrap
            success_opts = {'foreground': 'white', 'background': '#28a745'}  # Vert
            danger_opts = {'foreground': 'white', 'background': '#dc3545'}   # Rouge
            info_opts = {'foreground': 'white', 'background': '#17a2b8'}     # Bleu clair
            primary_opts = {'foreground': 'white', 'background': '#007bff'}  # Bleu

            self.style.configure('success.TButton', **success_opts)
            self.style.configure('danger.TButton', **danger_opts)
            self.style.configure('info.TButton', **info_opts)
            self.style.configure('primary.TButton', **primary_opts)

            # Appliquer les styles aux boutons
            btn_styles = {
                'start_button': 'success.TButton',
                'stop_button': 'danger.TButton',
                'scan_button': 'info.TButton',
                'export_scan_button': 'primary.TButton',
                'analyze_button': 'primary.TButton',
                'export_button': 'info.TButton'
            }

            for btn_name, style_name in btn_styles.items():
                btn = getattr(self, btn_name, None)
                if btn and isinstance(btn, (ttk.Button, ttkbootstrap.Button)):
                    btn.configure(style=style_name)

        except Exception as e:
            print(f"Error applying bootstrap styles: {e}")

    def create_theme_selector(self) -> None:
        """Create dropdown for theme selection"""
        try:
            theme_frame = ttk.Frame(self.master)
            theme_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

            # Style for theme selector
            self.style.configure("ThemeSelector.TLabel",
                               font=("Helvetica", 10),
                               padding=(5, 2))

            ttk.Label(theme_frame,
                     text="Thème :",
                     style="ThemeSelector.TLabel").pack(side=tk.LEFT, padx=5)

            # Get all themes as a flat list
            all_themes = [t for themes in self.available_themes.values() for t in themes]

            # Style for combobox
            self.style.configure("ThemeSelector.TCombobox",
                               padding=(5, 2),
                               arrowsize=12)

            self.theme_combobox = ttk.Combobox(
                theme_frame,
                textvariable=self.theme_var,
                values=all_themes,
                state="readonly",
                width=15,
                style="ThemeSelector.TCombobox"
            )
            self.theme_combobox.pack(side=tk.LEFT, padx=5)

            # Label to show theme category (Light/Dark)
            self.theme_category_label = ttk.Label(
                theme_frame,
                text="",
                style="ThemeSelector.TLabel"
            )
            self.theme_category_label.pack(side=tk.LEFT, padx=5)

            # Update category label for initial theme
            self._update_theme_category()

        except Exception as e:
            print(f"Error creating theme selector: {e}")

    def _on_theme_change(self, *args) -> None:
        """Callback when theme is changed"""
        if self._use_bootstrap:
            try:
                new_theme = self.theme_var.get()
                self.change_theme(new_theme)
            except Exception as e:
                print(f"Error in theme change callback: {e}")

    def _update_theme_category(self, *args) -> None:
        """Update the theme category label based on current theme"""
        if not hasattr(self, 'theme_category_label'):
            return

        try:
            current_theme = self.theme_var.get()
            category = next((cat for cat, themes in self.available_themes.items()
                         if current_theme in themes), "Unknown")
            self.theme_category_label.config(text=f"({category})")
        except Exception as e:
            print(f"Error updating theme category: {e}")

def main() -> None:
    """Point d'entrée autonome pour le test de l'interface bootstrap."""
    root = ttkbootstrap.Window(themename="darkly")
    app = BootstrapNetworkAnalyzerUI(master=root, theme="darkly")
    root.mainloop()

if __name__ == "__main__":
    main()

