import tkinter as tk
from tkinter import ttk
from utils.dialogs import show_info
import json
from utils.helpers import add_tooltip

FONT = ("Segoe UI", 10)

ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]
DEFAULT_MODES = ["mutations", "all_females", "stat_merge", "top_stat_females", "war", "automated"]

def build_tools_tab(app):
    row = 0

    ttk.Label(app.tab_tools, text="Default Settings for New Species:", font=("Segoe UI", 10, "bold")).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    row += 1

    template = app.settings.get("default_species_template", {})
    mode_defaults = set(template.get("modes", DEFAULT_MODES))
    app.default_mode_vars = {
        mode: tk.BooleanVar(value=(mode in mode_defaults))
        for mode in DEFAULT_MODES
    }
    ttk.Label(app.tab_tools, text="Enabled Modes:", font=FONT).grid(
        row=row, column=0, sticky="nw", padx=5, pady=2
    )
    col = 1
    app.default_mode_cbs = {}
    for mode in DEFAULT_MODES:
        cb = ttk.Checkbutton(app.tab_tools, text=mode, variable=app.default_mode_vars[mode])
        cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
        add_tooltip(cb, f"Enable {mode} mode for all new species")
        app.default_mode_cbs[mode] = cb
        col += 1

    def update_default_mode_state():
        disable = app.default_mode_vars["automated"].get()
        for m, cb in app.default_mode_cbs.items():
            if m == "automated":
                continue
            cb.configure(state="disabled" if disable else "normal")

    app.default_mode_cbs["automated"].configure(command=update_default_mode_state)
    update_default_mode_state()
    row += 1

    shared_defaults = set(template.get("stat_merge_stats", ALL_STATS))
    app.default_stat_vars = {
        stat: tk.BooleanVar(value=(stat in shared_defaults))
        for stat in ALL_STATS
    }

    ttk.Label(app.tab_tools, text="Shared Stats (merge/top/war):", font=FONT).grid(
        row=row, column=0, sticky="w", padx=5, pady=(10, 2)
    )
    row += 1
    sf = ttk.Frame(app.tab_tools)
    sf.grid(row=row, column=0, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = ttk.Checkbutton(sf, text=stat, variable=app.default_stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=10, pady=2)
        add_tooltip(cb, f"Include {stat} for new species by default")
    row += 1



    btn = ttk.Button(app.tab_tools, text="Apply These Defaults to New Species", command=lambda: set_defaults(app))
    btn.grid(row=row, column=0, pady=10)
    add_tooltip(btn, "Persist these defaults for future species")


def set_defaults(app):
    app.settings["default_species_template"] = {
        "modes": [mode for mode, var in app.default_mode_vars.items() if var.get()],
        "stat_merge_stats": [stat for stat, var in app.default_stat_vars.items() if var.get()],
        "top_stat_females_stats": [stat for stat, var in app.default_stat_vars.items() if var.get()],
        "war_stats": [stat for stat, var in app.default_stat_vars.items() if var.get()]
    }
    with open("settings.json", "w", encoding="utf-8") as f:
        json.dump(app.settings, f, indent=2)
    show_info("Defaults Saved", "Defaults for new species saved.")
