"""
Management of application configuration loaded from YAML.

This module provides the ConfigurationManager class which handles loading, saving,
and managing application configuration stored in YAML format. It includes support
for default values and configuration reset functionality.
"""

from tkinter import messagebox
from pathlib import Path
from typing import Dict, Any, Optional
from app_config import Constants, load_config, save_config, ConfigError


class ConfigurationManager:
    """
    Encapsulates application configuration loaded from YAML.

    This class provides methods to load, save, and manage application configuration.
    It maintains both the current configuration and a copy of the default values,
    allowing for configuration reset functionality.

    Attributes
    ----------
    path : Path
        Path to the configuration file.
    default_config : Dict[str, Any]
        Copy of the default configuration values.
    config : Dict[str, Any]
        Current active configuration.

    Methods
    -------
    load_config(filepath: Optional[Path] = None)
        Load configuration from a YAML file.
    save_config(filepath: Optional[Path] = None)
        Save current configuration to a YAML file.
    reset_to_default()
        Reset configuration to default values.
    get_config()
        Get the current configuration dictionary.
    update_config(key: str, value: Any)
        Update a specific configuration value.
    """

    def __init__(self, default_config: Optional[Dict[str, Any]] = None,
                 path: Path = Constants.CONFIG_PATH):
        """
        Initialize the configuration manager.

        Parameters
        ----------
        default_config : Dict[str, Any], optional
            Default configuration values. If None, loaded from the path.
        path : Path, optional
            Path to the configuration file. Defaults to Constants.CONFIG_PATH.
        """
        self.path = path
        self.default_config = default_config or load_config(path)
        self.config = self.default_config.copy()

    def load_config(self, filepath: Optional[Path] = None) -> None:
        """
        Load configuration from a YAML file.

        Parameters
        ----------
        filepath : Path, optional
            Path to the configuration file. If None, uses the instance's path.

        Raises
        ------
        ConfigError
            If there is an error loading the configuration file.
        """
        try:
            self.path = filepath or self.path
            self.config = load_config(self.path)
            messagebox.showinfo("Success", f"Configuration loaded from {self.path}.")
        except ConfigError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error loading configuration: {e}")

    def save_config(self, filepath: Optional[Path] = None) -> None:
        """
        Save current configuration to a YAML file.

        Parameters
        ----------
        filepath : Path, optional
            Path where to save the configuration. If None, uses the instance's path.

        Raises
        ------
        ConfigError
            If there is an error saving the configuration file.
        """
        try:
            self.path = filepath or self.path
            save_config(self.config, self.path)
            messagebox.showinfo("Success", f"Configuration saved to {self.path}.")
        except ConfigError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error saving configuration: {e}")

    def reset_to_default(self) -> None:
        """Reset the configuration to default values."""
        self.config = self.default_config.copy()
        messagebox.showinfo("Success", "Configuration reset to default values.")

    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.

        Returns
        -------
        Dict[str, Any]
            Current configuration dictionary.
        """
        return self.config

    def update_config(self, key: str, value: Any) -> None:
        """
        Update a specific configuration parameter.

        Parameters
        ----------
        key : str
            Configuration key to update.
        value : Any
            New value for the configuration key.

        Raises
        ------
        KeyError
            If the key does not exist in the configuration.
        """
        if key not in self.config:
            raise KeyError(f"Configuration key '{key}' does not exist.")
        self.config[key] = value
