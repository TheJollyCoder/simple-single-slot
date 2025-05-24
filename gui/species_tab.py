import json
import tkinter as tk
from tkinter import messagebox

ALL_MODES = ["mutations", "all_females", "stat_merge", "top_stat_females", "war"]
ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]

def build_species_tab(app):
    cfg   = app.config
    rules = cfg.rules

    # Species selector
    tk.Label(app.tab_species, text="Select Species:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    app.species_var = tk.StringVar()
    menu = tk.OptionMenu(app.tab_species, app.species_var, *sorted(rules.keys()))
    menu.grid(row=0, column=1, sticky="w")
    row = 1

    def load_species(name):
        spec = rules.get(name, {})
        for mode in ALL_MODES:
            app.mode_vars[mode].set(mode in spec.get("modes", []))
        for stat in ALL_STATS:
            app.mut_stat_vars[stat].set(stat in spec.get("mut_stats", []))
            app.top_stat_vars[stat].set(stat in spec.get("top_stats", []))

    def save_species():
        name = app.species_var.get()
        if not name:
            messagebox.showerror("Error", "No species selected.")
            return
        spec = rules.setdefault(name, {})
        spec["modes"]     = [m for m in ALL_MODES if app.mode_vars[m].get()]
        spec["mut_stats"] = [s for s in ALL_STATS if app.mut_stat_vars[s].get()]
        spec["top_stats"] = [s for s in ALL_STATS if app.top_stat_vars[s].get()]

        with open(cfg.rules_path, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=2)
        messagebox.showinfo("Saved", f"Species '{name}' settings saved.")

    # Mode checkboxes
    tk.Label(app.tab_species, text="Enabled Modes:").grid(row=row, column=0, sticky="w", pady=(5,0))
    col = 1
    for mode in ALL_MODES:
        cb = tk.Checkbutton(app.tab_species, text=mode, variable=app.mode_vars[mode])
        cb.grid(row=row, column=col, sticky="w", padx=2)
        col += 1
    row += 1

    # Mutation stats
    tk.Label(app.tab_species, text="Mutation Stats:").grid(row=row, column=0, sticky="nw", pady=(10,0))
    mf = tk.Frame(app.tab_species); mf.grid(row=row, column=1, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = tk.Checkbutton(mf, text=stat, variable=app.mut_stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)
    row += 1

    # Top stats
    tk.Label(app.tab_species, text="Top Stats:").grid(row=row, column=0, sticky="nw", pady=(10,0))
    tf = tk.Frame(app.tab_species); tf.grid(row=row, column=1, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = tk.Checkbutton(tf, text=stat, variable=app.top_stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)
    row += 1

    # Load & Save buttons
    tk.Button(app.tab_species, text="Load", command=lambda: load_species(app.species_var.get())) \
      .grid(row=row, column=0, pady=10)
    tk.Button(app.tab_species, text="Save", command=save_species) \
      .grid(row=row, column=1, pady=10)
