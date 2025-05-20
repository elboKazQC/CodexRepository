#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from bootstrap_ui import BootstrapNetworkAnalyzerUI

def main():
    """Point d'entrée de l'application avec interface bootstrap"""    # Crée l'interface en utilisant le thème sauvegardé dans la configuration
    app = BootstrapNetworkAnalyzerUI()
    app.master.mainloop()

if __name__ == "__main__":
    main()
