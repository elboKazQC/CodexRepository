#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour lancer l'application MoxaAnalyzerUI de manière simple
"""

import tkinter as tk
from tkinter import ttk
import os

class SimpleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lanceur d'application")
        
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Choisissez l'application à lancer", font=("Arial", 14)).pack(pady=10)
        
        ttk.Button(main_frame, text="Lancer Analyseur Moxa (Corrigé)", 
                  command=self.run_corrected_app).pack(fill=tk.X, pady=5)
        
        ttk.Button(main_frame, text="Lancer Analyseur Moxa (Simplifiée)", 
                  command=self.run_simple_app).pack(fill=tk.X, pady=5)
        
        ttk.Button(main_frame, text="Quitter", 
                  command=root.destroy).pack(fill=tk.X, pady=20)
        
        status_frame = ttk.Frame(root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = ttk.Label(status_frame, text="Prêt", anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
    
    def run_corrected_app(self):
        """Lance la version corrigée de l'application"""
        self.status_label.config(text="Lancement de la version corrigée...")
        try:
            self.root.destroy()  # Fermer cette fenêtre
            os.system('python "c:\\Users\\vcasaubon.NOOVELIA\\OneDrive - Noovelia\\Desktop\\AuditWifiApp\\runner_fixed_corrected.py"')
        except Exception as e:
            print(f"Erreur lors du lancement: {e}")
            
    def run_simple_app(self):
        """Lance la version simplifiée de l'application"""
        self.status_label.config(text="Lancement de la version simplifiée...")
        try:
            self.root.destroy()  # Fermer cette fenêtre
            os.system('python "c:\\Users\\vcasaubon.NOOVELIA\\OneDrive - Noovelia\\Desktop\\AuditWifiApp\\app_launcher.py"')
        except Exception as e:
            print(f"Erreur lors du lancement: {e}")

def main():
    root = tk.Tk()
    app = SimpleApp(root)
    root.geometry("400x300")
    root.mainloop()

if __name__ == "__main__":
    main()
