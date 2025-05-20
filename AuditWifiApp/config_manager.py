import json
import copy
from dataclasses import asdict
from tkinter import messagebox
from models import MoxaConfig

class ConfigurationManager:
    """
    Gère le chargement, la sauvegarde et la gestion des configurations.
    """

    def __init__(self, default_config: MoxaConfig):
        self.default_config = default_config
        self.config = copy.deepcopy(default_config)

    def load_config(self, filepath):
        """Charge une configuration à partir d'un fichier JSON."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.config = MoxaConfig.from_dict(data)
            messagebox.showinfo("Succès", f"Configuration chargée depuis {filepath}.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement de la configuration : {str(e)}")

    def save_config(self, filepath):
        """Sauvegarde la configuration actuelle dans un fichier JSON."""
        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(asdict(self.config), file, indent=2)
            messagebox.showinfo("Succès", f"Configuration sauvegardée dans {filepath}.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde de la configuration : {str(e)}")

    def reset_to_default(self):
        """Réinitialise la configuration aux valeurs par défaut."""
        self.config = copy.deepcopy(self.default_config)
        messagebox.showinfo("Succès", "Configuration réinitialisée aux valeurs par défaut.")

    def get_config(self):
        """Retourne la configuration actuelle."""
        return self.config

    def update_config(self, key, value):
        """Met à jour un paramètre spécifique de la configuration."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
        else:
            raise KeyError(f"La clé {key} n'existe pas dans la configuration.")
