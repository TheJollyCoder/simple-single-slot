import os
import json
import subprocess
import tkinter as tk
from tkinter import messagebox

ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]
ALL_MODES = ["mutations", "all_females", "stat_merge", "top_stat_females", "war"]

def build_tools_tab(app):
    cfg      = app.config
    settings = cfg.settings
    rules    = cfg.rules

    row = 0
    tk.Button(app.tab_tools, text="Run Calibration", command=lambda: run_calibration(cfg)) \
      .grid(row=row, column=0, sticky="w", padx=5, pady=5)
    row += 1

    tk.Button(app.tab_tools, text="Refresh Species List", command=lambda: refresh_species(cfg)) \
      .grid(row=row, column=0, sticky="w", padx=5)
    row += 1

    tk.Button(app.tab_tools, text="Save All Rules", command=lambda: save_all(cfg)) \
      .grid(row=row, column=0, sticky="w", padx=5)
    row += 2

    tk.Label(app.tab_tools, text="Defaults for New Species:", font=("Segoe UI", 11, "bold")) \
      .grid(row=row, column=0, sticky="w", pady=(10,5))
    row += 1

    # Default modes
    tk.Label(app.tab_tools, text="Enabled Modes:").grid(row=row, column=0, sticky="nw")
    app.default_mode_vars = {m: tk.BooleanVar(value=True) for m in ALL_MODES}
    col = 1
    for mode in ALL_MODES:
        cb = tk.Checkbutton(app.tab_tools, text=mode, variable=app.default_mode_vars[mode])
        cb.grid(row=row, column=col, sticky="w", padx=2)
        col += 1
    row += 1

    # Default mut_stats
    tk.Label(app.tab_tools, text="Mutation Stats:").grid(row=row, column=0, sticky="nw", pady=(5,0))
    app.default_mut_stats_vars = {s: tk.BooleanVar(value=True) for s in ALL_STATS}
    mf = tk.Frame(app.tab_tools); mf.grid(row=row, column=1, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = tk.Checkbutton(mf, text=stat, variable=app.default_mut_stats_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)
    row += 1

    # Default top_stats
    tk.Label(app.tab_tools, text="Top Stats:").grid(row=row, column=0, sticky="nw", pady=(5,0))
    app.default_top_stats_vars = {s: tk.BooleanVar(value=True) for s in ALL_STATS}
    tf = tk.Frame(app.tab_tools); tf.grid(row=row, column=1, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = tk.Checkbutton(tf, text=stat, variable=app.default_top_stats_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)
    row += 1

    tk.Button(app.tab_tools, text="Apply Defaults to New Species", command=lambda: set_defaults(cfg, app)) \
      .grid(row=row, column=0, columnspan=2, pady=10)

def run_calibration(cfg):
    try:
        script = os.path.join(os.path.dirname(cfg.settings_path), "setup_positions.py")
        subprocess.run(["python", script], check=True)
        messagebox.showinfo("Calibration", "Calibration complete. settings.json updated.")
    except Exception as e:
        messagebox.showerror("Calibration Error", str(e))

def refresh_species(cfg):
    added = 0
    for sp in cfg.progress.keys():
        if sp not in cfg.rules:
            cfg.rules[sp] = cfg.settings.get("default_species_template", {})
            added += 1
    if added:
        with open(cfg.rules_path, "w", encoding="utf-8") as f:
            json.dump(cfg.rules, f, indent=2)
    messagebox.showinfo("Refresh Species", f"{added} species added.")

def save_all(cfg):
    with open(cfg.rules_path, "w", encoding="utf-8") as f:
        json.dump(cfg.rules, f, indent=2)
    messagebox.showinfo("Save All", "All rules saved.")

def set_defaults(cfg, app):
    defaults = {
        "modes": [m for m, v in app.default_mode_vars.items() if v.get()],
        "mut_stats": [s for s, v in app.default_mut_stats_vars.items() if v.get()],
        "top_stats": [s for s, v in app.default_top_stats_vars.items() if v.get()]
    }
    cfg.settings["default_species_template"] = defaults
    with open(cfg.settings_path, "w", encoding="utf-8") as f:
        json.dump(cfg.settings, f, indent=2)
    messagebox.showinfo("Defaults Set", "Default species template updated.")
