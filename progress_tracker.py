from logger import get_logger
log = get_logger("progress_tracker")

import json
import os
import re
import time
from copy import deepcopy
from difflib import get_close_matches

HISTORY_FILE = "progress_history.json"

PROGRESS_FILE = "breeding_progress.json"
WIPE_DIR = "wipes"
RULES_FILE = "rules.json"

# default container for progress tracking per species
DEFAULT_PROGRESS_TEMPLATE = {
    "top_stats": {},
    "mutation_thresholds": {},
    "stud": {},
    "mutation_stud": {},
    "female_count": 0,
    "stop_female_count": 0,
    "stop_top_stat_females": 0,
}

def get_progress_file(wipe: str = "default") -> str:
    """Return the breeding progress path for a given wipe."""
    return os.path.join(WIPE_DIR, wipe, PROGRESS_FILE)


def get_history_file(wipe: str = "default") -> str:
    """Return the progress history path for a given wipe."""
    return os.path.join(WIPE_DIR, wipe, HISTORY_FILE)


def ensure_wipe_dir(wipe: str = "default") -> None:
    """Create wipe directory and empty files if missing."""
    os.makedirs(os.path.join(WIPE_DIR, wipe), exist_ok=True)
    for path in [get_progress_file(wipe), get_history_file(wipe)]:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)

def ensure_species(progress, species):
    """Ensure a species entry exists with all required keys."""
    if species not in progress:
        progress[species] = deepcopy(DEFAULT_PROGRESS_TEMPLATE)
        log.info(f"Added new species to progress: {species}")
    else:
        for k, v in DEFAULT_PROGRESS_TEMPLATE.items():
            progress[species].setdefault(k, v if isinstance(v, dict) else 0)

def load_progress(wipe: str = "default"):
    path = get_progress_file(wipe)
    ensure_wipe_dir(wipe)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)
            return {}
    return {}

def save_progress(data, wipe: str = "default"):
    ensure_wipe_dir(wipe)
    path = get_progress_file(wipe)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_history(wipe: str = "default"):
    path = get_history_file(wipe)
    ensure_wipe_dir(wipe)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(hist, wipe: str = "default"):
    ensure_wipe_dir(wipe)
    path = get_history_file(wipe)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2)

def record_history(species: str, category: str, stat: str, value: int, wipe: str = "default") -> None:
    hist = load_history(wipe)
    species_hist = hist.setdefault(species, {"top_stats": {}, "mutation_thresholds": {}})
    cat_hist = species_hist.setdefault(category, {}).setdefault(stat, [])
    cat_hist.append({"ts": int(time.time()), "value": value})
    save_history(hist, wipe)

def normalize_species_name(raw_name):
    """
    1) Strip off gender, CS prefix, parens, punctuation
    2) Fuzzy‐match the cleaned name against rules.json keys (if within ~20%)
    """
    # ─── Basic cleaning ─────────────────────────────
    parts = re.sub(r"\(.*?\)", "", raw_name)
    parts = re.sub(r"\b(male|female)\b", "", parts, flags=re.IGNORECASE)
    parts = parts.replace("CS", "").strip()
    cleaned = re.sub(r"[^\w\s]", "", parts).strip()

    # ─── Fuzzy match to existing species keys ───────
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            rules = json.load(f)
        candidates = list(rules.keys())
        # cutoff=0.8 catches up to ~2–3 char differences
        matches = get_close_matches(cleaned, candidates, n=1, cutoff=0.8)
        if matches:
            return matches[0]
    except Exception:
        pass

    return cleaned

def update_top_stats(egg, scan_stats, progress, wipe: str = "default"):
    s = normalize_species_name(egg)
    updated = False
    log.debug(f"Evaluating top stats for {s}")
    ensure_species(progress, s)

    for stat, values in scan_stats.items():
        base = values.get("base", 0)
        if base <= 0:
            continue
        current = progress[s]["top_stats"].get(stat, 0)
        if base > current:
            log.info(f"New top stat for {stat}: {base} (was {current})")
            progress[s]["top_stats"][stat] = base
            record_history(s, "top_stats", stat, base, wipe)
            updated = True

    return updated

def update_mutation_thresholds(egg, scan_stats, config, progress, sex, wipe: str = "default"):
    if sex != "male":
        return False
    s = normalize_species_name(egg)
    updated = False
    log.debug(f"Evaluating mutation thresholds for {s}")
    ensure_species(progress, s)

    mutation_stats = config.get("mutation_stats", [])
    for stat in mutation_stats:
        mut = scan_stats.get(stat, {}).get("mutation", 0)
        if mut <= 0:
            continue
        current = progress[s]["mutation_thresholds"].get(stat, 0)
        if mut > current:
            log.info(f"New threshold for {stat}: {mut} (was {current})")
            progress[s]["mutation_thresholds"][stat] = mut
            record_history(s, "mutation_thresholds", stat, mut, wipe)
            updated = True

    return updated

def update_stud(egg, scan_stats, config, progress, wipe: str = "default"):
    s = normalize_species_name(egg)
    ensure_species(progress, s)

    merge_stats = config.get("stat_merge_stats", [])
    top_stats = progress[s]["top_stats"]
    stud = progress[s].get("stud", {})

    match_count = sum(
        1 for stat in merge_stats
        if scan_stats.get(stat, {}).get("base", 0) >= top_stats.get(stat, 0)
    )

    stud_count = sum(
        1 for stat in merge_stats
        if stud.get(stat, 0) >= top_stats.get(stat, 0)
    )

    if match_count > stud_count or (
        match_count == stud_count and match_count > 0 and any(
            scan_stats.get(stat, {}).get("base", 0) > stud.get(stat, 0)
            for stat in merge_stats
        )
    ):
        if match_count > stud_count:
            log.info(
                f"New stud accepted for {s} with {match_count} top stat matches"
            )
        else:
            for stat in merge_stats:
                base = scan_stats.get(stat, {}).get("base", 0)
                if base > stud.get(stat, 0):
                    log.info(
                        f"New stud accepted for {s}; {stat} base {base}>{stud.get(stat, 0)}"
                    )
                    break
        new_stud = {
            stat: scan_stats.get(stat, {}).get("base", 0)
            for stat in merge_stats
        }
        progress[s]["stud"] = new_stud
        progress[s]["top_stats"] = {
            stat: val for stat, val in new_stud.items() if val > 0
        }
        for stat, val in progress[s]["top_stats"].items():
            record_history(s, "top_stats", stat, val, wipe)
        return True

    return False

def update_mutation_stud(egg, scan_stats, config, progress):
    """Update mutation stud bases when mutations equal thresholds."""
    s = normalize_species_name(egg)
    ensure_species(progress, s)

    mutation_stats = config.get("mutation_stats", [])
    thresholds = progress[s].get("mutation_thresholds", {})
    mstud = progress[s].get("mutation_stud", {})

    updated = False

    for stat in mutation_stats:
        mut = scan_stats.get(stat, {}).get("mutation", 0)
        base = scan_stats.get(stat, {}).get("base", 0)
        thresh = thresholds.get(stat, 0)
        if mut == thresh and base > mstud.get(stat, 0):
            log.info(
                f"New mutation stud for {s} {stat}: base {base} at {mut} mutations"
            )
            progress[s].setdefault("mutation_stud", {})[stat] = base
            updated = True

    return updated

def increment_female_count(egg, progress, sex):
    """Increment female count for a species if sex is female."""
    if sex != "female":
        return 0
    s = normalize_species_name(egg)
    ensure_species(progress, s)
    progress[s]["female_count"] += 1
    log.info(f"Female count for {s} is now {progress[s]['female_count']}")
    return progress[s]["female_count"]


def apply_automated_modes(female_count, modes):
    """Return mode set adjusted for automated breeding rules."""
    modes = set(modes)
    if "automated" not in modes:
        return modes

    if female_count < 5:
        modes.update({"mutations", "stat_merge", "all_females"})
        modes.discard("top_stat_females")
    elif female_count < 96:
        modes.update({"mutations", "stat_merge", "top_stat_females"})
        modes.discard("all_females")
    else:
        modes = {"war"} if "war" in modes else set()

    return modes

def adjust_rules_for_females(species, progress, rules, default_template=None):
    """Adjust breeding rules based on female counts."""
    if species not in rules:
        if default_template:
            rules[species] = deepcopy(default_template)
        else:
            return False
        modes = set(rules[species].get("modes", []))
        modes.add("automated")
        rules[species]["modes"] = list(modes)

    ensure_species(progress, species)
    count = progress[species].get("female_count", 0)
    modes = set(rules[species].get("modes", []))
    before = modes.copy()

    modes = apply_automated_modes(count, modes)

    if modes != before:
        rules[species]["modes"] = list(modes)
        log.info(f"Rules updated for {species}: {rules[species]['modes']}")
        return True

    return False
