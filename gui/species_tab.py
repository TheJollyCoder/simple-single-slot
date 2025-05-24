import json
import tkinter as tk
from tkinter import messagebox

# These must match your ALL_MODES and ALL_STATS elsewhere
ALL_MODES = ["mutations", "all_females", "stat_merge", "top_stat_females", "war"]
ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]

def build_species_tab(app):
    cfg   = app.config
    rules = cfg.rules

    # --- Species selector ---
    tk.Label(app.tab_species, text="Select Species:") \
      .grid(row=0, column=0, sticky="w", padx=5, pady=5)

    app.species_var = tk.StringVar()
    menu = tk.OptionMenu(app.tab_species, app.species_var, *sorted(rules.keys()))
    menu.grid(row=0, column=1, sticky="w", padx=5, pady=5)

    # Track last for auto-save
    app._last_species = None

    def load_species(name):
        """Populate the UI from rules[name]."""
        spec = rules.get(name, {})
        for mode in ALL_MODES:
            app.mode_vars[mode].set(mode in spec.get("modes", []))
        for stat in ALL_STATS:
            app.mut_stat_vars[stat].set(stat in spec.get("mut_stats", []))
            app.top_stat_vars[stat].set(stat in spec.get("top_stats", []))

    def save_species(name):
        """Write current UI settings back to rules[name]."""
        if not name:
            return
        spec = rules.setdefault(name, {})
        spec["modes"]     = [m for m in ALL_MODES if app.mode_vars[m].get()]
        spec["mut_stats"] = [s for s in ALL_STATS if app.mut_stat_vars[s].get()]
        spec["top_stats"] = [s for s in ALL_STATS if app.top_stat_vars[s].get()]

        with open(cfg.rules_path, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=2)

    def on_species_change(*_):
        new = app.species_var.get()
        # Auto-save old
        if app._last_species and app._last_species != new:
            save_species(app._last_species)
        # Auto-load new
        if new:
            load_species(new)
            app._last_species = new

    # Watch for selection changes
    app.species_var.trace_add("write", on_species_change)

    # --- Mode checkboxes ---
    row = 1
    tk.Label(app.tab_species, text="Enabled Modes:") \
      .grid(row=row, column=0, sticky="w", pady=(5,0))
    col = 1
    for mode in ALL_MODES:
        cb = tk.Checkbutton(app.tab_species, text=mode, variable=app.mode_vars[mode])
        cb.grid(row=row, column=col, sticky="w", padx=4)
        col += 1
    row += 1

    # --- Mutation stats checkboxes ---
    tk.Label(app.tab_species, text="Mutation Stats:") \
      .grid(row=row, column=0, sticky="nw", pady=(10,0))
    mf = tk.Frame(app.tab_species)
    mf.grid(row=row, column=1, sticky="w", pady=(10,0))
    for i, stat in enumerate(ALL_STATS):
        cb = tk.Checkbutton(mf, text=stat, variable=app.mut_stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)
    row += 1

    # --- Top stats checkboxes ---
    tk.Label(app.tab_species, text="Top Stats:") \
      .grid(row=row, column=0, sticky="nw", pady=(10,0))
    tf = tk.Frame(app.tab_species)
    tf.grid(row=row, column=1, sticky="w", pady=(10,0))
    for i, stat in enumerate(ALL_STATS):
        cb = tk.Checkbutton(tf, text=stat, variable=app.top_stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)
    row += 1

    # --- Manual Save button (optional) ---
    tk.Button(app.tab_species, text="Save Species Settings",
              command=lambda: save_species(app.species_var.get())) \
      .grid(row=row, column=0, columnspan=2, pady=10)
