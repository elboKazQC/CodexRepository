from dataclasses import dataclass, asdict
from typing import Any, Dict

@dataclass
class MoxaConfig:
    """Configuration parameters for a Moxa device."""
    min_transmission_rate: int
    max_transmission_power: int
    rts_threshold: int
    fragmentation_threshold: int
    roaming_mechanism: str
    roaming_difference: int
    remote_connection_check: bool
    wmm_enabled: bool
    turbo_roaming: bool
    ap_alive_check: bool

    def to_dict(self) -> Dict[str, Any]:
        """Return the configuration as a plain dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MoxaConfig":
        """Create a ``MoxaConfig`` instance from a dictionary."""
        return MoxaConfig(**data)
