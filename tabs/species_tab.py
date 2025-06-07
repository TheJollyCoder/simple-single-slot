import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
from progress_tracker import normalize_species_name

DEFAULT_MODES = ["mutations", "all_females", "stat_merge", "top_stat_females", "war"]
ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]

def build_species_tab(app):
    row = 0
    tk.Label(app.tab_species, text="Select Species:").grid(row=row, column=0, sticky="w")
    app.selected_species = tk.StringVar()
    # Track last-loaded species for autosave
    app._last_species = None

    app.species_list = list(app.rules.keys())
    app.species_dropdown = ttk.Combobox(
        app.tab_species,
        values=app.species_list,
        textvariable=app.selected_species,
        state="readonly"
    )
    app.species_dropdown.grid(row=row, column=1, sticky="w")
    row += 1

    # Checkbox vars
    app.mode_vars = {mode: tk.BooleanVar() for mode in DEFAULT_MODES}
    app.stat_vars = {stat: tk.BooleanVar() for stat in ALL_STATS}
    app.mutation_stat_vars = {stat: tk.BooleanVar() for stat in ALL_STATS}

    # Placeholders for load/save buttons (now optional)
    tk.Label(app.tab_species, text="Enabled Modes:").grid(row=row, column=0, sticky="nw")
    col = 1
    for mode in DEFAULT_MODES:
        tk.Checkbutton(app.tab_species, text=mode, variable=app.mode_vars[mode]).grid(
            row=row, column=col, sticky="w"
        )
        col += 1
    row += 1

    tk.Label(app.tab_species, text="Shared Stats (merge/top/war):").grid(row=row, column=0, sticky="nw")
    sf = tk.Frame(app.tab_species)
    sf.grid(row=row, column=1, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        tk.Checkbutton(sf, text=stat, variable=app.stat_vars[stat]).grid(
            row=i//3, column=i%3, sticky="w", padx=5, pady=1
        )
    row += 1

    tk.Label(app.tab_species, text="Mutation Stats:").grid(row=row, column=0, sticky="nw")
    mf = tk.Frame(app.tab_species)
    mf.grid(row=row, column=1, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        tk.Checkbutton(mf, text=stat, variable=app.mutation_stat_vars[stat]).grid(
            row=i//3, column=i%3, sticky="w", padx=5, pady=1
        )
    row += 1

    # Optional manual save button (can hide if you don't need it)
    tk.Button(app.tab_species, text="Save Species Config", command=lambda: save_species_config(app)).grid(
        row=row, column=0, pady=10
    )

    def on_species_select(event):
        new = app.selected_species.get()
        # autosave previous species
        old = app._last_species
        if old:
            rule = {
                "modes": [m for m, var in app.mode_vars.items() if var.get()],
                "mutation_stats": [s for s, var in app.mutation_stat_vars.items() if var.get()],
                "stat_merge_stats": [s for s, var in app.stat_vars.items() if var.get()],
                "top_stat_females_stats": [s for s, var in app.stat_vars.items() if var.get()],
                "war_stats": [s for s, var in app.stat_vars.items() if var.get()]
            }
            app.rules[old] = rule
            rules_file = BASE_DIR / "rules.json"
            with rules_file.open("w", encoding="utf-8") as f:
                json.dump(app.rules, f, indent=2)
        # load new
        app._last_species = new
        load_species_config(app)

    app.species_dropdown.bind("<<ComboboxSelected>>", on_species_select)


def load_species_config(app):
    s = app.selected_species.get()
    rule = app.rules.get(s, {})
    for mode in DEFAULT_MODES:
        app.mode_vars[mode].set(mode in rule.get("modes", []))
    for stat in ALL_STATS:
        app.stat_vars[stat].set(stat in rule.get("stat_merge_stats", []))
        app.mutation_stat_vars[stat].set(stat in rule.get("mutation_stats", []))


def save_species_config(app):
    s = app.selected_species.get()
    if not s:
        messagebox.showwarning("No species", "Select a species first.")
        return
    app.rules[s] = {
        "modes": [m for m, var in app.mode_vars.items() if var.get()],
        "mutation_stats": [s for s, var in app.mutation_stat_vars.items() if var.get()],
        "stat_merge_stats": [s for s, var in app.stat_vars.items() if var.get()],
        "top_stat_females_stats": [s for s, var in app.stat_vars.items() if var.get()],
        "war_stats": [s for s, var in app.stat_vars.items() if var.get()]
    }
    rules_file = BASE_DIR / "rules.json"
    with rules_file.open("w", encoding="utf-8") as f:
        json.dump(app.rules, f, indent=2)
    messagebox.showinfo("Saved", f"Settings for {s} updated.")
