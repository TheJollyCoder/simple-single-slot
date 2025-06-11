import logging
import json

# load your settings once
try:
    with open("settings.json", encoding="utf-8") as f:
        cfg = json.load(f)
except FileNotFoundError:
    cfg = {}

debug_flags = cfg.get("debug_mode", False)

# Default to WARNING so only important events show when debug flags are off
logging.getLogger().setLevel(logging.WARNING)

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
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger
