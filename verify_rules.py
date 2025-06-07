#!/usr/bin/env python3
"""Check which breeding modes would keep a given egg.

Usage:
  python verify_rules.py "Species Name" male --stat health=35+2 --stat stamina=30

Run without --stat options to be prompted interactively for each stat.
"""
import argparse
import json
import os

from breeding_logic import should_keep_egg
from progress_tracker import load_progress, normalize_species_name

ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]

RULES_FILE = "rules.json"
SETTINGS_FILE = "settings.json"

def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def parse_stat(text: str):
    name, val = text.split("=", 1)
    name = name.lower()
    base, mut = 0, 0
    if "+" in val:
        base, mut = val.split("+", 1)
    elif "/" in val:
        base, mut = val.split("/", 1)
    else:
        base = val
    return name, {"base": int(base), "mutation": int(mut)}

def collect_stats(args):
    stats = {s: {"base": 0, "mutation": 0} for s in ALL_STATS}
    if args.stat:
        for s in args.stat:
            k, v = parse_stat(s)
            if k in stats:
                stats[k] = v
    else:
        print("Enter base or base+mut for each stat (blank to skip):")
        for st in ALL_STATS:
            inp = input(f"  {st}: ").strip()
            if inp:
                k, v = parse_stat(f"{st}={inp}")
                stats[k] = v
    return stats

def main():
    parser = argparse.ArgumentParser(description="Verify breeding rules")
    parser.add_argument("species", help="Species name as shown in game")
    parser.add_argument("sex", choices=["male", "female"], help="Egg sex")
    parser.add_argument(
        "--stat",
        action="append",
        metavar="STAT=BASE+MUT",
        help="Provide stat values (can repeat). Example: --stat health=35+2",
    )
    args = parser.parse_args()

    stats = collect_stats(args)
    progress = load_progress()
    rules = load_rules()
    settings = load_settings()

    species_norm = normalize_species_name(args.species)
    config = rules.get(species_norm, settings.get("default_species_template", {}))

    scan = {
        "egg": args.species,
        "sex": args.sex,
        "stats": stats,
        "updated_stats": False,
        "updated_thresholds": False,
        "updated_stud": False,
    }

    decision, reasons = should_keep_egg(scan, config, progress)

    print(f"Normalized species: {species_norm}")
    print(f"Overall decision: {decision.upper()}")
    for mode in ["mutations", "all_females", "stat_merge", "top_stat_females", "war"]:
        if reasons.get(mode):
            print(f"  ✔ would keep via {mode}")
    for k, v in reasons.get("_debug", {}).items():
        print(f"  debug[{k}]: {v}")

if __name__ == "__main__":
    main()
