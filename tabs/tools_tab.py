import tkinter as tk
from tkinter import messagebox
import json
import subprocess
from pathlib import Path
from utils.helpers import refresh_species_dropdown

BASE_DIR = Path(__file__).resolve().parent.parent

ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]
DEFAULT_MODES = ["mutations", "all_females", "stat_merge", "top_stat_females", "war"]

def build_tools_tab(app):
    row = 0
    tk.Button(app.tab_tools, text="Run Calibration", command=run_calibration).grid(row=row, column=0, sticky="w")
    row += 1
    tk.Button(app.tab_tools, text="Refresh from Progress", command=lambda: refresh_species(app)).grid(row=row, column=0, sticky="w")
    row += 1
    tk.Button(app.tab_tools, text="Save All Settings", command=lambda: save_all(app)).grid(row=row, column=0, sticky="w")
    row += 2
    tk.Label(app.tab_tools, text="Default Settings for New Species:", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w")
    row += 1

    app.default_mode_vars = {mode: tk.BooleanVar(value=True) for mode in DEFAULT_MODES}
    tk.Label(app.tab_tools, text="Enabled Modes:").grid(row=row, column=0, sticky="nw")
    col = 1
    for mode in DEFAULT_MODES:
        cb = tk.Checkbutton(app.tab_tools, text=mode, variable=app.default_mode_vars[mode])
        cb.grid(row=row, column=col, sticky="w")
        col += 1
    row += 1

    app.default_stat_vars = {stat: tk.BooleanVar(value=True) for stat in ALL_STATS}
    app.default_mutation_vars = {stat: tk.BooleanVar(value=True) for stat in ALL_STATS}

    tk.Label(app.tab_tools, text="Shared Stats (merge/top/war):").grid(row=row, column=0, sticky="w", pady=(10, 2))
    row += 1
    sf = tk.Frame(app.tab_tools)
    sf.grid(row=row, column=0, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = tk.Checkbutton(sf, text=stat, variable=app.default_stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=10, pady=2)
    row += 1

    tk.Label(app.tab_tools, text="Mutation Stats:").grid(row=row, column=0, sticky="w", pady=(10, 2))
    row += 1
    mf = tk.Frame(app.tab_tools)
    mf.grid(row=row, column=0, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = tk.Checkbutton(mf, text=stat, variable=app.default_mutation_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=10, pady=2)
    row += 1

    tk.Button(app.tab_tools, text="Apply These Defaults to New Species", command=lambda: set_defaults(app)).grid(row=row, column=0, pady=10)

def run_calibration():
    try:
        subprocess.run(["python", "setup_positions.py"], check=True)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def refresh_species(app):
    from progress_tracker import load_progress
    progress = load_progress()
    new_added = 0
    default = app.settings.get("default_species_template", {})
    for species in progress:
        if species not in app.rules:
            app.rules[species] = default.copy()
            new_added += 1
    rules_file = BASE_DIR / "rules.json"
    with rules_file.open("w", encoding="utf-8") as f:
        json.dump(app.rules, f, indent=2)
    from utils.helpers import refresh_species_dropdown
    refresh_species_dropdown(app)
    messagebox.showinfo("Refreshed", f"Added {new_added} new species.")

def save_all(app):
    app.settings["hotkey_scan"] = app.hotkey_var.get()
    app.settings["popup_delay"] = app.popup_delay_var.get()
    app.settings["action_delay"] = app.action_delay_var.get()
    app.settings["scan_loop_delay"] = app.scan_loop_delay_var.get()
    app.settings["debug_mode"] = {k: v.get() for k, v in app.debug_vars.items()}
    settings_file = BASE_DIR / "settings.json"
    with settings_file.open("w", encoding="utf-8") as f:
        json.dump(app.settings, f, indent=2)
    messagebox.showinfo("Saved", "All settings saved.")

def set_defaults(app):
    app.settings["default_species_template"] = {
        "modes": [mode for mode, var in app.default_mode_vars.items() if var.get()],
        "mutation_stats": [stat for stat, var in app.default_mutation_vars.items() if var.get()],
        "stat_merge_stats": [stat for stat, var in app.default_stat_vars.items() if var.get()],
        "top_stat_females_stats": [stat for stat, var in app.default_stat_vars.items() if var.get()],
        "war_stats": [stat for stat, var in app.default_stat_vars.items() if var.get()]
    }
    settings_file = BASE_DIR / "settings.json"
    with settings_file.open("w", encoding="utf-8") as f:
        json.dump(app.settings, f, indent=2)
    messagebox.showinfo("Defaults Saved", "Defaults for new species saved.")
