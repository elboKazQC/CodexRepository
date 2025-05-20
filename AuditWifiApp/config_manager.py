"""Management of application configuration loaded from YAML."""

from tkinter import messagebox
from pathlib import Path
from app_config import CONFIG_PATH, load_config, save_config


class ConfigurationManager:
    """Encapsulates application configuration loaded from YAML."""

    def __init__(self, default_config: dict | None = None, path: Path = CONFIG_PATH):
        """Initialise le gestionnaire avec les valeurs par défaut."""
        self.path = path
        self.default_config = default_config or load_config(path)
        self.config = self.default_config.copy()

    def load_config(self, filepath: Path | None = None) -> None:
        """Charge une configuration à partir d'un fichier YAML."""
        try:
            self.path = filepath or self.path
            self.config = load_config(self.path)
            messagebox.showinfo("Succès", f"Configuration chargée depuis {self.path}.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement de la configuration : {str(e)}")

    def save_config(self, filepath: Path | None = None) -> None:
        """Sauvegarde la configuration actuelle dans un fichier YAML."""
        try:
            self.path = filepath or self.path
            save_config(self.config, self.path)
            messagebox.showinfo("Succès", f"Configuration sauvegardée dans {self.path}.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde de la configuration : {str(e)}")

    def reset_to_default(self) -> None:
        """Réinitialise la configuration aux valeurs par défaut."""
        self.config = self.default_config.copy()
        messagebox.showinfo("Succès", "Configuration réinitialisée aux valeurs par défaut.")

    def get_config(self) -> dict:
        """Retourne la configuration actuelle."""
        return self.config

    def update_config(self, key: str, value) -> None:
        """Met à jour un paramètre spécifique de la configuration."""
        if key in self.config:
            self.config[key] = value
        else:
            raise KeyError(f"La clé {key} n'existe pas dans la configuration.")
