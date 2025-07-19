import os
from typing import Any, Dict, Optional

import yaml

class Config:
    """
    Common configuration loader for Merlai.
    Loads YAML config from a default or specified path and provides access to config sections.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.expanduser("~/.merlai/config.yaml")
        self.data: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.config_path):
            self.data = {}
            return
        with open(self.config_path, "r") as f:
            self.data = yaml.safe_load(f) or {}

    def get(self, section: str, default: Any = None) -> Any:
        """
        Get a section from the config (e.g., 'ai_models', 'plugins').
        Returns default if not found.
        """
        return self.data.get(section, default)

    def reload(self) -> None:
        """
        Reload the config file from disk.
        """
        self._load()
