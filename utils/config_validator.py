# config_validator.py - checks config files for required keys and types

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List


def _check_type(value: Any, expected_type: Iterable[type]) -> bool:
    return isinstance(value, tuple(expected_type))


def validate_settings(settings: Dict[str, Any]) -> List[str]:
    """Validate settings.json content."""
    required = {
        "slot_x": int,
        "slot_y": int,
        "destroy_offsets": list,
        "destroy_this_offsets": list,
        "popup_delay": (int, float),
        "action_delay": (int, float),
        "hotkey_scan": str,
        "debug_mode": (bool, dict),
        "webhook_url": str,
        "drop_all_button": list,
        "drop_all_confirm": list,
        "food_slots": list,
        "species_roi": dict,
        "stat_rois": dict,
        "ocr": dict,
    }
    warnings: List[str] = []
    for key, typ in required.items():
        if key not in settings:
            warnings.append(f"settings.json missing key: {key}")
            continue
        if not _check_type(settings[key], typ if isinstance(typ, tuple) else (typ,)):
            warnings.append(f"settings.json key '{key}' has wrong type")
    return warnings


def validate_rules(rules: Dict[str, Any]) -> List[str]:
    """Validate rules.json content."""
    warnings: List[str] = []
    if not isinstance(rules, dict):
        return ["rules.json must contain a JSON object"]
    req_fields = [
        "modes",
        "mutation_stats",
        "stat_merge_stats",
        "top_stat_females_stats",
        "war_stats",
    ]
    for species, cfg in rules.items():
        if not isinstance(cfg, dict):
            warnings.append(f"rules.json entry for '{species}' is not an object")
            continue
        for f in req_fields:
            if f not in cfg:
                warnings.append(f"rules.json '{species}' missing '{f}'")
            elif not isinstance(cfg[f], list):
                warnings.append(f"rules.json '{species}' field '{f}' should be a list")
    return warnings


def validate_progress(progress: Dict[str, Any]) -> List[str]:
    """Validate breeding_progress.json content."""
    warnings: List[str] = []
    if not isinstance(progress, dict):
        return ["breeding_progress.json must contain a JSON object"]
    req = ["top_stats", "mutation_thresholds", "stud"]
    for species, data in progress.items():
        if not isinstance(data, dict):
            warnings.append(f"breeding_progress.json entry for '{species}' is not an object")
            continue
        for f in req:
            if f not in data:
                warnings.append(f"breeding_progress.json '{species}' missing '{f}'")
            elif not isinstance(data[f], dict):
                warnings.append(
                    f"breeding_progress.json '{species}' field '{f}' should be an object"
                )
    return warnings


def validate_configs(settings: Dict[str, Any], rules: Dict[str, Any], progress: Dict[str, Any]) -> List[str]:
    """Return list of warnings for all configs."""
    warnings: List[str] = []
    warnings.extend(validate_settings(settings))
    warnings.extend(validate_rules(rules))
    warnings.extend(validate_progress(progress))
    return warnings
