"""Bootstrap-based UI module for the AuditWifiApp.

This module provides a UI built with ttkbootstrap. It reuses the
NetworkAnalyzerUI logic but initializes the interface with a themed
``Window`` when ttkbootstrap is available. If ttkbootstrap is not
installed, it falls back to standard Tkinter widgets.
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional

from runner import NetworkAnalyzerUI

try:
    from ttkbootstrap import Window, Style
    BOOTSTRAP_AVAILABLE = True
except Exception:  # pragma: no cover - library may be missing
    BOOTSTRAP_AVAILABLE = False
    Window = tk.Tk  # type: ignore
    Style = tk.ttk.Style  # type: ignore


class BootstrapNetworkAnalyzerUI(NetworkAnalyzerUI):
    """UI using ttkbootstrap for improved styling."""

    def __init__(self, master: Optional[tk.Tk] = None, theme: str = "flatly"):
        if master is None:
            if BOOTSTRAP_AVAILABLE:
                master = Window(themename=theme)
            else:  # fallback to classic Tk
                master = tk.Tk()
        self._use_bootstrap = BOOTSTRAP_AVAILABLE
        super().__init__(master)

    def setup_style(self) -> None:
        """Configure styles for the interface."""
        if self._use_bootstrap:
            style = Style()
            style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
            style.configure("Alert.TLabel", foreground="red", font=("Helvetica", 12))
            style.configure("Stats.TLabel", font=("Helvetica", 10))
            style.configure("Analyze.TButton", font=("Helvetica", 12), padding=10)
        else:
            super().setup_style()

