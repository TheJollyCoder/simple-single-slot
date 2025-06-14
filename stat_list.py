#!/usr/bin/env python3
import json
import os

from typing import List

from progress_tracker import load_progress

PROGRESS_FILE = "breeding_progress.json"  # unused but kept for compatibility
RULES_FILE = "rules.json"
SETTINGS_FILE = "settings.json"
OUTPUT_FILE = "stat_list.txt"

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
    print("Choose display mode:")
    print("  1) full      — show every stud & mutation stat")
    print("  2) mutation  — only stats in each species' mutation_stats")
    choice = input("Enter 1 or 2: ").strip()
    mode = "mutation" if choice == "2" else "full"
    settings["stat_list_mode"] = mode
    save_settings(settings)
    return mode


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


def generate_stat_list(progress, rules, settings) -> List[str]:
    """Return formatted stat list lines based on progress and rules."""
    mode = settings.get("stat_list_mode", "full")

    lines: List[str] = []
    for species in sorted(progress):
        stud = progress[species].get("stud", {})
        thresh = progress[species].get("mutation_thresholds", {})

        if mode == "mutation":
            muts = rules.get(species, {}).get("mutation_stats")
            if muts:
                tokens = format_mutation(stud, thresh, muts)
            else:
                tokens = format_full(stud, thresh)
        else:
            tokens = format_full(stud, thresh)

        if tokens:
            lines.append(f"{' '.join(tokens)} {species}")

    extra = settings.get("custom_stat_list_lines", [])
    if isinstance(extra, list):
        lines.extend(extra)

    return lines

def main():
    # load files
    settings = load_json(SETTINGS_FILE)
    progress = load_progress(settings.get("current_wipe", "default"))
    mode = get_mode(settings)
    rules = load_json(RULES_FILE) if mode == "mutation" else {}
    settings["stat_list_mode"] = mode

    lines = generate_stat_list(progress, rules, settings)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))

    print(f"Wrote {len(lines)} lines to '{OUTPUT_FILE}' in {mode!r} mode.")

if __name__ == "__main__":
    main()
