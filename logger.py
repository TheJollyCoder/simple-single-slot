import logging
import json
from pathlib import Path

# load your settings once using a path relative to this file
BASE_DIR = Path(__file__).resolve().parent
settings_file = BASE_DIR / "settings.json"
with settings_file.open(encoding="utf-8") as f:
    cfg = json.load(f)
debug_flags = cfg.get("debug_mode", {})


def get_logger(module_name: str) -> logging.Logger:
    # if debug_flags is a dict, look up per-module;
    # if it's a bool, apply it to everything.
    if isinstance(debug_flags, dict):
        enabled = debug_flags.get(module_name, False)
    else:
        enabled = bool(debug_flags)

    level = logging.DEBUG if enabled else logging.INFO

    logger = logging.getLogger(module_name)
    # avoid adding multiple handlers if called repeatedly
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "%(asctime)s [%(levelname)s] %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger
