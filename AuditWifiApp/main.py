#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import tkinter as tk

# Ensure local virtual environment packages are available
_venv_path = os.path.join(os.path.dirname(__file__), "..", ".venv", "lib",
                        f"python{sys.version_info.major}.{sys.version_info.minor}",
                        "site-packages")
if os.path.isdir(_venv_path) and _venv_path not in sys.path:
    sys.path.insert(0, _venv_path)

from bootstrap_ui import BootstrapNetworkAnalyzerUI

def main() -> None:
    """Launch the application using the configured bootstrap interface."""
    # Create the UI using the theme stored in the configuration
    app = BootstrapNetworkAnalyzerUI()
    app.master.mainloop()

if __name__ == "__main__":
    main()
