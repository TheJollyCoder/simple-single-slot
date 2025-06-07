#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from logger import get_logger

log = get_logger("stat_list")

BASE_DIR = Path(__file__).resolve().parent
PROGRESS_FILE     = BASE_DIR / "breeding_progress.json"
EXTRA_TAMES_FILE  = BASE_DIR / "extra_tames.json"
RULES_FILE        = BASE_DIR / "rules.json"
SETTINGS_FILE     = BASE_DIR / "settings.json"
OUTPUT_FILE       = BASE_DIR / "stat_list.txt"

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

def get_mode(settings):
    m = settings.get("stat_list_mode")
    if m in ("full", "mutation"):
        return m
    log.info("Choose display mode:")
    log.info("  1) full      — show every stud & mutation stat")
    log.info("  2) mutation  — only stats in each species' mutation_stats")
    choice = input("Enter 1 or 2: ").strip()
    mode = "mutation" if choice == "2" else "full"
    settings["stat_list_mode"] = mode
    save_settings(settings)
    return mode

def merge_extra(progress):
    extra = load_json(EXTRA_TAMES_FILE)
    for sp, data in extra.items():
        if sp not in progress:
            progress[sp] = data
    return progress

def format_full(stud, thresh):
    tokens = []
    for stat in sorted(set(stud) | set(thresh)):
        L = stat[0].upper()
        b = stud.get(stat)
        m = thresh.get(stat)
        if b is not None and m is not None:
            tokens.append(f"{b}+{m}{L}")
        elif b is not None:
            tokens.append(f"{b}{L}")
        else:
            tokens.append(f"+{m}{L}")
    return tokens

def format_mutation(stud, thresh, mutation_stats):
    tokens = []
    for stat in mutation_stats:
        L = stat[0].upper()
        b = stud.get(stat)
        m = thresh.get(stat)
        if b is None and m is None:
            continue
        if b is not None and m is not None:
            tokens.append(f"{b}+{m}{L}")
        elif b is not None:
            tokens.append(f"{b}{L}")
        else:
            tokens.append(f"+{m}{L}")
    return tokens

def main():
    # load files
    progress = load_json(PROGRESS_FILE)
    progress = merge_extra(progress)
    settings = load_json(SETTINGS_FILE)
    mode     = get_mode(settings)
    rules    = load_json(RULES_FILE) if mode == "mutation" else {}

    lines = []
    for species in sorted(progress):
        stud   = progress[species].get("stud", {})
        thresh = progress[species].get("mutation_thresholds", {})

        if mode == "mutation":
            muts = rules.get(species, {}).get("mutation_stats", None)
            if muts:  
                tokens = format_mutation(stud, thresh, muts)
            else:
                # fallback for species without mutation_stats
                tokens = format_full(stud, thresh)
        else:
            tokens = format_full(stud, thresh)

        if tokens:
            lines.append(f"{' '.join(tokens)} {species}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))

    log.info("Wrote %d lines to '%s' in %r mode.", len(lines), OUTPUT_FILE, mode)

if __name__ == "__main__":
    main()
