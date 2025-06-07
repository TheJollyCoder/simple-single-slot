from logger import get_logger
log = get_logger("progress_tracker")

import json
import os
import re
import time
from difflib import get_close_matches

HISTORY_FILE = "progress_history.json"

PROGRESS_FILE = "breeding_progress.json"
RULES_FILE = "rules.json"

# default container for progress tracking per species
DEFAULT_PROGRESS_TEMPLATE = {
    "top_stats": {},
    "mutation_thresholds": {},
    "stud": {},
    "female_count": 0,
}

def ensure_species(progress, species):
    """Ensure a species entry exists with all required keys."""
    if species not in progress:
        progress[species] = DEFAULT_PROGRESS_TEMPLATE.copy()
    else:
        for k, v in DEFAULT_PROGRESS_TEMPLATE.items():
            progress[species].setdefault(k, v if isinstance(v, dict) else 0)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(data):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(hist):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2)

def record_history(species: str, category: str, stat: str, value: int) -> None:
    hist = load_history()
    species_hist = hist.setdefault(species, {"top_stats": {}, "mutation_thresholds": {}})
    cat_hist = species_hist.setdefault(category, {}).setdefault(stat, [])
    cat_hist.append({"ts": int(time.time()), "value": value})
    save_history(hist)

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

def update_top_stats(egg, scan_stats, progress):
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
            record_history(s, "top_stats", stat, base)
            updated = True

    return updated

def update_mutation_thresholds(egg, scan_stats, config, progress, sex):
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
            record_history(s, "mutation_thresholds", stat, mut)
            updated = True

    return updated

def update_stud(egg, scan_stats, config, progress):
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

    if match_count > stud_count:
        log.info(f"New stud accepted for {s} with {match_count} top stat matches")
        progress[s]["stud"] = {
            stat: scan_stats.get(stat, {}).get("base", 0)
            for stat in merge_stats
        }
        return True

    return False

def increment_female_count(egg, progress, sex):
    """Increment female count for a species if sex is female."""
    if sex != "female":
        return 0
    s = normalize_species_name(egg)
    ensure_species(progress, s)
    progress[s]["female_count"] += 1
    log.info(f"Female count for {s} is now {progress[s]['female_count']}")
    return progress[s]["female_count"]

def adjust_rules_for_females(species, progress, rules, default_template=None):
    """Adjust breeding rules based on female counts."""
    if species not in rules:
        if default_template:
            rules[species] = default_template.copy()
        else:
            return False
        modes = set(rules[species].get("modes", []))
        modes.add("automated")
        rules[species]["modes"] = list(modes)

    ensure_species(progress, species)
    count = progress[species].get("female_count", 0)
    modes = set(rules[species].get("modes", []))
    before = modes.copy()

    if "automated" in modes:
        if count < 30:
            modes.update({"mutations", "stat_merge", "all_females"})
            modes.discard("top_stat_females")
        elif count < 96:
            modes.update({"mutations", "stat_merge", "top_stat_females"})
            modes.discard("all_females")
        else:
            modes.update({"mutations", "stat_merge"})
            modes.discard("all_females")
            modes.discard("top_stat_females")
            modes.discard("automated")

    if modes != before:
        rules[species]["modes"] = list(modes)
        log.info(f"Rules updated for {species}: {rules[species]['modes']}")
        return True

    return False
