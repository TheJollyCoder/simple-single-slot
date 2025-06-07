import tkinter as tk
from tkinter import ttk, messagebox
from utils.dialogs import show_error, show_warning, show_info

from utils.helpers import refresh_species_dropdown, add_tooltip

FONT = ("Segoe UI", 10)
import json
from progress_tracker import normalize_species_name
DEFAULT_MODES = ["mutations", "all_females", "stat_merge", "top_stat_females", "war"]
ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]

def build_species_tab(app):
    row = 0
    ttk.Label(app.tab_species, text="Select Species:", font=FONT).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    app.selected_species = tk.StringVar()
    # Track last-loaded species for autosave
    app._last_species = None

    app.species_list = list(app.rules.keys())
    app.species_dropdown = ttk.Combobox(
        app.tab_species,
        values=app.species_list,
        textvariable=app.selected_species,
        state="readonly",
        width=30,
    )
    app.species_dropdown.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    add_tooltip(app.species_dropdown, "Select the species whose rules you want to edit")
    row += 1

    # Checkbox vars
    app.mode_vars = {mode: tk.BooleanVar() for mode in DEFAULT_MODES}
    app.stat_vars = {stat: tk.BooleanVar() for stat in ALL_STATS}
    app.mutation_stat_vars = {stat: tk.BooleanVar() for stat in ALL_STATS}

    # Placeholders for load/save buttons (now optional)
    ttk.Label(app.tab_species, text="Enabled Modes:", font=FONT).grid(
        row=row, column=0, sticky="nw", padx=5, pady=2
    )
    col = 1
    for mode in DEFAULT_MODES:
        cb = ttk.Checkbutton(app.tab_species, text=mode, variable=app.mode_vars[mode])
        cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
        add_tooltip(cb, f"Enable the {mode} mode for this species")
        col += 1
    row += 1

    ttk.Label(app.tab_species, text="Shared Stats (merge/top/war):", font=FONT).grid(
        row=row, column=0, sticky="nw", padx=5, pady=(10, 2)
    )
    sf = ttk.Frame(app.tab_species)
    sf.grid(row=row, column=1, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = ttk.Checkbutton(sf, text=stat, variable=app.stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=1)
        add_tooltip(cb, f"Track {stat} when merging or rating dinos")
    row += 1

    ttk.Label(app.tab_species, text="Mutation Stats:", font=FONT).grid(
        row=row, column=0, sticky="nw", padx=5, pady=(10, 2)
    )
    mf = ttk.Frame(app.tab_species)
    mf.grid(row=row, column=1, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = ttk.Checkbutton(mf, text=stat, variable=app.mutation_stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=1)
        add_tooltip(cb, f"Monitor mutations affecting {stat}")
    row += 1

    # Optional manual save button (can hide if you don't need it)
    ttk.Button(app.tab_species, text="Save Species Config", command=lambda: save_species_config(app)).grid(
        row=row, column=0, pady=10
    )
    ttk.Button(app.tab_species, text="Delete Species", command=lambda: delete_species(app)).grid(
        row=row, column=1, pady=10
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
            with open("rules.json", "w", encoding="utf-8") as f:
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
        show_warning("No species", "Select a species first.")
        return
    app.rules[s] = {
        "modes": [m for m, var in app.mode_vars.items() if var.get()],
        "mutation_stats": [s for s, var in app.mutation_stat_vars.items() if var.get()],
        "stat_merge_stats": [s for s, var in app.stat_vars.items() if var.get()],
        "top_stat_females_stats": [s for s, var in app.stat_vars.items() if var.get()],
        "war_stats": [s for s, var in app.stat_vars.items() if var.get()]
    }
    with open("rules.json", "w", encoding="utf-8") as f:
        json.dump(app.rules, f, indent=2)
    show_info("Saved", f"Settings for {s} updated.")

def delete_species(app):
    s = app.selected_species.get()
    if not s:
        show_warning("No species", "Select a species first.")
        return
    if not messagebox.askyesno("Confirm", f"Delete configuration for {s}?"):
        return
    if s in app.rules:
        del app.rules[s]
        with open("rules.json", "w", encoding="utf-8") as f:
            json.dump(app.rules, f, indent=2)
    app.selected_species.set("")
    app._last_species = None
    refresh_species_dropdown(app)
