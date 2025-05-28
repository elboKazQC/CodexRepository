import json
import os
import re
import shutil
from typing import Dict, Optional

MAC_FILE = "mac_tags.json"
BACKUP_FILE = "mac_tags_backup.json"

class MacTagManager:
    """Manage MAC address tags and persistence."""

    def __init__(self, file_path: str = MAC_FILE):
        self.file_path = file_path
        self.backup_file = BACKUP_FILE
        self.tags: Dict[str, str] = {}
        self.load_tags()

    def load_tags(self) -> None:
        """Load tags from disk, creating an empty file if needed."""
        if not os.path.exists(self.file_path):
            self.tags = {}
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.tags = json.load(f)
        except Exception:
            self.tags = {}
            try:
                shutil.copy(self.file_path, self.backup_file)
            except Exception:
                pass

    def save_tags(self) -> None:
        """Save tags to disk and create a backup."""
        try:
            if os.path.exists(self.file_path):
                shutil.copy(self.file_path, self.backup_file)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.tags, f, indent=2)
        except Exception as e:
            print(f"Failed to save MAC tags: {e}")

    @staticmethod
    def validate_mac(mac: str) -> bool:
        """Validate MAC address format (AA:BB:CC:DD:EE:FF)."""
        return bool(re.fullmatch(r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", mac))

    def get_tag(self, mac: str) -> Optional[str]:
        """Return tag associated with MAC if any."""
        return self.tags.get(mac.upper())

    def set_tag(self, mac: str, tag: str) -> bool:
        """Add or update tag for MAC address. Returns True on success."""
        if not self.validate_mac(mac):
            return False
        self.tags[mac.upper()] = tag.strip()
        return True

    def delete_tag(self, mac: str) -> None:
        """Remove tag for MAC address."""
        self.tags.pop(mac.upper(), None)
