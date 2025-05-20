import yaml
from pathlib import Path

# Path to the YAML configuration file
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load configuration from YAML file.

    Parameters
    ----------
    path : Path, optional
        Location of the configuration file. Defaults to ``CONFIG_PATH``.

    Returns
    -------
    dict
        Parsed configuration dictionary or empty dict if file is missing.
    """
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def save_config(config: dict, path: Path = CONFIG_PATH) -> None:
    """Save configuration dictionary back to YAML file."""
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(config, fh, allow_unicode=True)
