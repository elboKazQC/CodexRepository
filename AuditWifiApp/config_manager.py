import json
from tkinter import messagebox

class ConfigurationManager:
    """
    Gère le chargement, la sauvegarde et la gestion des configurations.
    """

    def __init__(self, default_config):
        self.default_config = default_config
        self.config = default_config.copy()

    def load_config(self, filepath):
        """Charge une configuration à partir d'un fichier JSON."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                self.config = json.load(file)
            messagebox.showinfo("Succès", f"Configuration chargée depuis {filepath}.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement de la configuration : {str(e)}")

    def save_config(self, filepath):
        """Sauvegarde la configuration actuelle dans un fichier JSON."""
        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(self.config, file, indent=2)
            messagebox.showinfo("Succès", f"Configuration sauvegardée dans {filepath}.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde de la configuration : {str(e)}")

    def reset_to_default(self):
        """Réinitialise la configuration aux valeurs par défaut."""
        self.config = self.default_config.copy()
        messagebox.showinfo("Succès", "Configuration réinitialisée aux valeurs par défaut.")

    def get_config(self):
        """Retourne la configuration actuelle."""
        return self.config

    def update_config(self, key, value):
        """Met à jour un paramètre spécifique de la configuration."""
        if key in self.config:
            self.config[key] = value
        else:
            raise KeyError(f"La clé {key} n'existe pas dans la configuration.")
