#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Entry point for the WiFi Network Analyzer application.

This module sets up the Python environment and launches the main application window.
It ensures the virtual environment packages are available by adding the appropriate
path to sys.path if necessary.
"""

import os
import sys
import tkinter as tk
from pathlib import Path
from typing import Optional


def get_venv_site_packages() -> Optional[Path]:
    """
    Get the virtual environment's site-packages directory.

    Returns
    -------
    Optional[Path]
        Path to the site-packages directory if found, None otherwise.

    Notes
    -----
    The virtual environment is expected to be in a .venv directory at the
    project root, following standard Python virtual environment structure.
    """
    venv_path = Path(__file__).parent.parent / ".venv" / "lib" / \
        f"python{sys.version_info.major}.{sys.version_info.minor}" / \
        "site-packages"

    try:
        if venv_path.is_dir():
            return venv_path
    except Exception as e:
        print(f"Warning: Error checking virtual environment path: {e}", file=sys.stderr)
    return None


def setup_environment() -> None:
    """
    Configure the Python environment for the application.

    This function ensures that packages from the virtual environment are available
    by adding the site-packages directory to sys.path if needed.
    """
    venv_site_packages = get_venv_site_packages()
    if venv_site_packages and str(venv_site_packages) not in sys.path:
        sys.path.insert(0, str(venv_site_packages))


def main() -> None:
    """
    Launch the application using the configured bootstrap interface.

    This function creates and runs the main application window using the
    theme stored in the configuration.
    """
    setup_environment()
    from bootstrap_ui import BootstrapNetworkAnalyzerUI

    app = BootstrapNetworkAnalyzerUI()
    app.master.mainloop()


if __name__ == "__main__":
    main()
