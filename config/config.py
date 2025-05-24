import json
import os
from utils.logger import get_logger

log = get_logger("config")

class Config:
    def __init__(self, project_root=None):
        root = project_root or os.path.dirname(__file__)
        self.settings_path = os.path.join(root, "settings.json")
        self.rules_path    = os.path.join(root, "rules.json")
        self.progress_path = os.path.join(root, "breeding_progress.json")

        self.settings = self._load_json(self.settings_path)
        self.rules    = self._load_json(self.rules_path)
        self.progress = self._load_json(self.progress_path)

        # Apply per-module log levels (default INFO)
        lvl_map = {"CRITICAL":50, "ERROR":40, "WARNING":30, "INFO":20, "DEBUG":10}
        for mod, lvl in self.settings.get("log_levels", {}).items():
            get_logger(mod).setLevel(lvl_map.get(lvl.upper(),20))

    def _load_json(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Failed loading JSON {path}", exc_info=e)
            return {}

    def save_progress(self):
        try:
            with open(self.progress_path, "w", encoding="utf-8") as f:
                json.dump(self.progress, f, indent=2)
        except Exception as e:
            log.error("Failed saving progress", exc_info=e)
