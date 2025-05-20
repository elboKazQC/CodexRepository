#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from bootstrap_ui import BootstrapNetworkAnalyzerUI

def main():
    """Point d'entrée de l'application avec interface bootstrap"""
    app = BootstrapNetworkAnalyzerUI(theme="darkly")  # Utilise le thème sombre par défaut
    app.master.mainloop()

if __name__ == "__main__":
    main()
