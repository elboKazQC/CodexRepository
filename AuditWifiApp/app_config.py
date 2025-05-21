"""
Application configuration management module.

This module provides functionality to load, save and manage application
configuration through YAML files. It includes a constants class for centralized
configuration values and utility functions for config file operations.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - only for hints
    from config_manager import ConfigurationManager


class Constants:
    """
    Central storage for application-wide constants.

    This class provides a single point of truth for configuration values and
    paths used throughout the application.

    Attributes
    ----------
    CONFIG_PATH : Path
        Path to the main YAML configuration file.
    DEFAULT_ENCODING : str
        Default character encoding for file operations.
    """
    CONFIG_PATH = Path(__file__).parent / "config.yaml"
    DEFAULT_ENCODING = "utf-8"

# Backward compatibility constant
CONFIG_PATH = Constants.CONFIG_PATH


def load_config(path: Path = Constants.CONFIG_PATH) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Parameters
    ----------
    path : Path, optional
        Location of the configuration file. Defaults to ``Constants.CONFIG_PATH``.

    Returns
    -------
    Dict[str, Any]
        Parsed configuration dictionary or empty dict if file is missing.

    Notes
    -----
    If the configuration file does not exist, an empty dictionary is returned
    instead of raising an error. This allows for graceful handling of missing
    configuration files.
    """
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding=Constants.DEFAULT_ENCODING) as fh:
            return yaml.safe_load(fh) or {}
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to load configuration from {path}: {e}") from e


def save_config(config: Dict[str, Any], path: Path = Constants.CONFIG_PATH) -> None:
    """
    Save configuration dictionary to a YAML file.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary to save.
    path : Path, optional
        Target path for the configuration file. Defaults to ``Constants.CONFIG_PATH``.

    Raises
    ------
    ConfigError
        If there is an error writing the configuration file.
    """
    try:
        with path.open("w", encoding=Constants.DEFAULT_ENCODING) as fh:
            yaml.safe_dump(config, fh, allow_unicode=True)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to save configuration to {path}: {e}") from e


def create_manager(path: Path = Constants.CONFIG_PATH) -> 'ConfigurationManager':
    """
    Create a ConfigurationManager instance using defaults from YAML.

    Parameters
    ----------
    path : Path, optional
        Path to the configuration file. Defaults to ``Constants.CONFIG_PATH``.

    Returns
    -------
    ConfigurationManager
        A new configuration manager initialized with the specified config file.
    """
    from config_manager import ConfigurationManager
    return ConfigurationManager(load_config(path))


class ConfigError(Exception):
    """Exception raised for configuration-related errors."""
    pass
