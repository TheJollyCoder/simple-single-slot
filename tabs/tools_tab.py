import tkinter as tk
from tkinter import ttk
from utils.dialogs import show_error, show_info
import json
import subprocess
from utils.helpers import refresh_species_dropdown, add_tooltip

FONT = ("Segoe UI", 10)

ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]
DEFAULT_MODES = ["mutations", "all_females", "stat_merge", "top_stat_females", "war"]

def build_tools_tab(app):
    row = 0
    btn = ttk.Button(app.tab_tools, text="Run Calibration", command=run_calibration)
    btn.grid(row=row, column=0, sticky="w", padx=5, pady=2)
    add_tooltip(btn, "Run setup_positions.py to calibrate UI coordinates")
    row += 1

    btn = ttk.Button(app.tab_tools, text="Refresh from Progress", command=lambda: refresh_species(app))
    btn.grid(row=row, column=0, sticky="w", padx=5, pady=2)
    add_tooltip(btn, "Create rules entries from progress.json")
    row += 1

    btn = ttk.Button(app.tab_tools, text="Save All Settings", command=lambda: save_all(app))
    btn.grid(row=row, column=0, sticky="w", padx=5, pady=2)
    add_tooltip(btn, "Write all current settings to disk")
    row += 2

    ttk.Label(app.tab_tools, text="Default Settings for New Species:", font=("Segoe UI", 10, "bold")).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    row += 1

    app.default_mode_vars = {mode: tk.BooleanVar(value=True) for mode in DEFAULT_MODES}
    ttk.Label(app.tab_tools, text="Enabled Modes:", font=FONT).grid(
        row=row, column=0, sticky="nw", padx=5, pady=2
    )
    col = 1
    for mode in DEFAULT_MODES:
        cb = ttk.Checkbutton(app.tab_tools, text=mode, variable=app.default_mode_vars[mode])
        cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
        add_tooltip(cb, f"Default enable {mode} mode")
        col += 1
    row += 1

    app.default_stat_vars = {stat: tk.BooleanVar(value=True) for stat in ALL_STATS}
    app.default_mutation_vars = {stat: tk.BooleanVar(value=True) for stat in ALL_STATS}

    ttk.Label(app.tab_tools, text="Shared Stats (merge/top/war):", font=FONT).grid(
        row=row, column=0, sticky="w", padx=5, pady=(10, 2)
    )
    row += 1
    sf = ttk.Frame(app.tab_tools)
    sf.grid(row=row, column=0, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = ttk.Checkbutton(sf, text=stat, variable=app.default_stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=10, pady=2)
        add_tooltip(cb, f"Track {stat} by default")
    row += 1

    ttk.Label(app.tab_tools, text="Mutation Stats:", font=FONT).grid(
        row=row, column=0, sticky="w", padx=5, pady=(10, 2)
    )
    row += 1
    mf = ttk.Frame(app.tab_tools)
    mf.grid(row=row, column=0, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = ttk.Checkbutton(mf, text=stat, variable=app.default_mutation_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=10, pady=2)
        add_tooltip(cb, f"Default mutation stat {stat}")
    row += 1

    btn = ttk.Button(app.tab_tools, text="Apply These Defaults to New Species", command=lambda: set_defaults(app))
    btn.grid(row=row, column=0, pady=10)
    add_tooltip(btn, "Save defaults for new species to settings.json")

def run_calibration():
    try:
        subprocess.run(["python", "setup_positions.py"], check=True)
    except Exception as e:
        show_error("Error", str(e))

def refresh_species(app):
    from progress_tracker import load_progress
    progress = load_progress()
    new_added = 0
    default = app.settings.get("default_species_template", {})
    for species in progress:
        if species not in app.rules:
            app.rules[species] = default.copy()
            new_added += 1
    with open("rules.json", "w", encoding="utf-8") as f:
        json.dump(app.rules, f, indent=2)
    from utils.helpers import refresh_species_dropdown
    refresh_species_dropdown(app)
    show_info("Refreshed", f"Added {new_added} new species.")

def save_all(app):
    app.settings["hotkey_scan"] = app.hotkey_var.get()
    app.settings["popup_delay"] = app.popup_delay_var.get()
    app.settings["action_delay"] = app.action_delay_var.get()
    app.settings["scan_loop_delay"] = app.scan_loop_delay_var.get()
    app.settings["debug_mode"] = {k: v.get() for k, v in app.debug_vars.items()}
    with open("settings.json", "w", encoding="utf-8") as f:
        json.dump(app.settings, f, indent=2)
    show_info("Saved", "All settings saved.")

def set_defaults(app):
    app.settings["default_species_template"] = {
        "modes": [mode for mode, var in app.default_mode_vars.items() if var.get()],
        "mutation_stats": [stat for stat, var in app.default_mutation_vars.items() if var.get()],
        "stat_merge_stats": [stat for stat, var in app.default_stat_vars.items() if var.get()],
        "top_stat_females_stats": [stat for stat, var in app.default_stat_vars.items() if var.get()],
        "war_stats": [stat for stat, var in app.default_stat_vars.items() if var.get()]
    }
    with open("settings.json", "w", encoding="utf-8") as f:
        json.dump(app.settings, f, indent=2)
    show_info("Defaults Saved", "Defaults for new species saved.")
