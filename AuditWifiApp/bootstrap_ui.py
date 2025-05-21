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
        # Define available themes
        self.available_themes = {
            "Light": ["cosmo", "flatly", "litera", "minty", "lumen", "sandstone"],
            "Dark": ["darkly", "cyborg", "vapor", "solar", "superhero"]
        }

        # Create a flat list of all themes
        all_themes = [theme for category in self.available_themes.values() for theme in category]

        # Load config and validate theme
        self._config = load_config()
        config_theme = self._config.get("interface", {}).get("theme", "darkly")

        # Validate and set theme
        self._theme = theme or config_theme
        if self._theme not in all_themes:
            self._theme = "darkly"  # Default to darkly if invalid theme
            self._config["interface"]["theme"] = self._theme
            save_config(self._config)

        # Initialize bootstrap availability
        self._use_bootstrap = BOOTSTRAP_AVAILABLE

        # Initialize window with validated theme
        if master is None:
            if self._use_bootstrap:
                try:
                    master = ttkbootstrap.Window(themename=self._theme)
                    master.title("AuditWifiApp")
                    master.geometry("1200x800")  # Set initial window size
                except Exception as e:
                    print(f"Error initializing theme {self._theme}: {e}")
                    self._theme = "darkly"
                    master = ttkbootstrap.Window(themename=self._theme)
            else:
                master = tk.Tk()
                master.title("AuditWifiApp")
                master.geometry("1200x800")

        # Initialize theme-related components before parent
        if self._use_bootstrap:
            try:
                self.style = Style(theme=self._theme)
            except Exception as e:
                print(f"Error setting style with theme {self._theme}: {e}")
                self.style = Style(theme="darkly")
        else:
            self.style = ttk.Style()

        # Initialize theme variable
        self.theme_var = tk.StringVar(master=master, value=self._theme)
        if self._use_bootstrap:
            self.theme_var.trace_add("write", self._on_theme_change)

        # Initialize parent class last
        super().__init__(master)

    def configure_styles(self):
        """Configure all ttk styles"""
        if self._use_bootstrap:
            # Bootstrap-specific styles
            success_opts = {"padding": 5}
            danger_opts = {"padding": 5}
            info_opts = {"padding": 5}

            # Label styles
            self.style.configure("TLabel", font=("Helvetica", 10))
            self.style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
            self.style.configure("Subtitle.TLabel", font=("Helvetica", 12, "bold"))
            self.style.configure("Stats.TLabel", font=("Helvetica", 10))

            # Button styles
            self.style.configure('success.TButton', **success_opts)
            self.style.configure('danger.TButton', **danger_opts)
            self.style.configure('info.TButton', **info_opts)

            # Theme selector styles
            self.style.configure("ThemeSelector.TLabel",
                               font=("Helvetica", 10),
                               padding=5)
            self.style.configure("ThemeSelector.TCombobox",
                               padding=5)

            # Notebook styles
            self.style.configure("TNotebook", padding=2)
            self.style.configure("TNotebook.Tab", padding=(10, 4))

            # Fix combobox width
            self.style.configure('TCombobox', postoffset=(0, 0, 150, 0))  # Limit dropdown width    def create_interface(self) -> None:
        """Create the interface with bootstrap styles."""
        # Create the base interface first (including notebook and tabs)
        super().create_interface()

        if self._use_bootstrap:
            # Configure styles
            self.configure_styles()

            # Create theme selector at the top
            self.create_theme_selector()

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

    def _on_theme_change(self, *args) -> None:
        """Handle theme changes."""
        if not self._use_bootstrap:
            return

        try:
            new_theme = self.theme_var.get()
            self.style.theme_use(new_theme)
            self._theme = new_theme

            # Update config
            if "interface" not in self._config:
                self._config["interface"] = {}
            self._config["interface"]["theme"] = new_theme
            save_config(self._config)

            # Update the theme category display
            self._update_theme_category()
        except Exception as e:
            print(f"Error in theme change callback: {e}")

    def _update_theme_category(self, *args) -> None:
        """Update the theme category label based on current theme"""
        if not hasattr(self, "theme_category_label"):
            return

        current_theme = self.theme_var.get()
        category = next(
            (cat for cat, themes in self.available_themes.items()
             if current_theme in themes),
            "Unknown"
        )
        self.theme_category_label.configure(text=f"Category: {category}")

    def create_theme_selector(self) -> None:
        """Create the theme selector widgets"""
        if not self._use_bootstrap:
            return

        # Create frame for theme selection with fixed width
        theme_frame = ttk.Frame(self.master)
        theme_frame.pack(fill=tk.X, padx=5, pady=2)

        # Theme selector label
        ttk.Label(
            theme_frame,
            text="Theme:",
            style="ThemeSelector.TLabel"
        ).pack(side=tk.LEFT, padx=(5,2))

        # All available themes
        all_themes = [theme for themes in self.available_themes.values()
                     for theme in themes]

        # Theme selector combobox with fixed width
        theme_select = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=all_themes,
            state="readonly",
            style="ThemeSelector.TCombobox",
            width=15  # Fixed width
        )
        theme_select.pack(side=tk.LEFT, padx=2)

        # Theme category label with fixed width
        self.theme_category_label = ttk.Label(
            theme_frame,
            text="",
            style="ThemeSelector.TLabel",
            width=15  # Fixed width
        )
        self.theme_category_label.pack(side=tk.LEFT, padx=2)

        # Update category display
        self._update_theme_category()

def main() -> None:
    """Point d'entrée autonome pour le test de l'interface bootstrap."""
    root = ttkbootstrap.Window(themename="darkly")
    app = BootstrapNetworkAnalyzerUI(master=root, theme="darkly")
    root.mainloop()

if __name__ == "__main__":
    main()

