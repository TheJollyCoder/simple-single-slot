from logger import get_logger
log = get_logger("progress_tracker")

import json
import os
import re
from difflib import get_close_matches

PROGRESS_FILE = "breeding_progress.json"
RULES_FILE    = "rules.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(data):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

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
    if s not in progress:
        progress[s] = {"top_stats": {}, "mutation_thresholds": {}, "stud": {}}

    for stat, values in scan_stats.items():
        base = values.get("base", 0)
        if base <= 0:
            continue
        current = progress[s]["top_stats"].get(stat, 0)
        if base > current:
            log.info(f"New top stat for {stat}: {base} (was {current})")
            progress[s]["top_stats"][stat] = base
            updated = True

    return updated

def update_mutation_thresholds(egg, scan_stats, config, progress, sex):
    if sex != "male":
        return False
    s = normalize_species_name(egg)
    updated = False
    log.debug(f"Evaluating mutation thresholds for {s}")
    if s not in progress:
        progress[s] = {"top_stats": {}, "mutation_thresholds": {}, "stud": {}}

    mutation_stats = config.get("mutation_stats", [])
    for stat in mutation_stats:
        mut = scan_stats.get(stat, {}).get("mutation", 0)
        if mut <= 0:
            continue
        current = progress[s]["mutation_thresholds"].get(stat, 0)
        if mut > current:
            log.info(f"New threshold for {stat}: {mut} (was {current})")
            progress[s]["mutation_thresholds"][stat] = mut
            updated = True

    return updated

def update_stud(egg, scan_stats, config, progress):
    s = normalize_species_name(egg)
    if s not in progress:
        progress[s] = {"top_stats": {}, "mutation_thresholds": {}, "stud": {}}

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
