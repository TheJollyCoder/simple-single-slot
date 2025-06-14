import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import simpledialog
from utils.dialogs import show_error, show_warning, show_info

from utils.helpers import refresh_species_dropdown, add_tooltip

FONT = ("Segoe UI", 10)
import json
from progress_tracker import normalize_species_name
import progress_tracker

ALWAYS_ON_MODES = ["mutations", "stat_merge"]
DEFAULT_MODES = ["all_females", "top_stat_females", "war", "automated"]
ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]

def build_species_tab(app):
    row = 0
    ttk.Label(app.tab_species, text="Search:", font=FONT).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    app.search_var = tk.StringVar()
    search_entry = ttk.Entry(app.tab_species, textvariable=app.search_var, width=30)
    search_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    add_tooltip(search_entry, "Filter the species list")
    row += 1

    ttk.Label(app.tab_species, text="Select Species:", font=FONT).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    app.selected_species = tk.StringVar()
    # Track last-loaded species for autosave
    app._last_species = None

    # populate dropdown using only the current wipe's progress
    app.progress = progress_tracker.load_progress(app.settings.get("current_wipe", "default"))
    app.species_list = sorted(app.progress.keys())
    app.species_dropdown = ttk.Combobox(
        app.tab_species,
        values=app.species_list,
        textvariable=app.selected_species,
        state="readonly",
        width=30,
    )
    app.species_dropdown.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    add_tooltip(app.species_dropdown, "Select the species whose rules you want to edit. Use search to filter")

    def update_species_dropdown(_=None):
        query = app.search_var.get().lower()
        if query:
            values = [s for s in app.species_list if query in s.lower()]
        else:
            values = list(app.species_list)
        app.species_dropdown["values"] = values

    app.update_species_dropdown = update_species_dropdown
    search_entry.bind("<KeyRelease>", update_species_dropdown)
    update_species_dropdown()
    row += 1

    # ---- Sub-tabs for rules vs automation ----
    nb = ttk.Notebook(app.tab_species)
    nb.grid(row=row, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
    app.rules_frame = ttk.Frame(nb)
    app.auto_frame = ttk.Frame(nb)
    nb.add(app.rules_frame, text="Rules")
    nb.add(app.auto_frame, text="Auto")
    row_auto = 0
    row_rules = 0

    # Automatic breeding variables
    app.auto_var = tk.BooleanVar()
    app.female_count_var = tk.IntVar()
    app.stop_females_var = tk.IntVar()
    app.stop_top_var = tk.IntVar()

    def on_stop_change(*_):
        species = app.selected_species.get()
        if not species:
            return
        prog = app.progress.setdefault(species, {})
        prog["stop_female_count"] = app.stop_females_var.get()
        prog["stop_top_stat_females"] = app.stop_top_var.get()
        progress_tracker.save_progress(app.progress, app.settings.get("current_wipe", "default"))

    app.stop_females_var.trace_add("write", on_stop_change)
    app.stop_top_var.trace_add("write", on_stop_change)

    # List of all species with auto toggle
    app.auto_species_vars = {}
    list_frame = ttk.LabelFrame(app.auto_frame, text="Species List")
    list_frame.grid(row=row_auto, column=3, rowspan=6, sticky="nw", padx=10)
    for i, sp in enumerate(app.species_list):
        var = tk.BooleanVar(value="automated" in app.rules.get(sp, {}).get("modes", []))
        def _make_toggle(sp=sp, var=var):
            def _toggle():
                modes = set(app.rules.get(sp, {}).get("modes", []))
                if var.get():
                    modes.add("automated")
                else:
                    modes.discard("automated")
                app.rules.setdefault(sp, {})["modes"] = list(modes)
                with open("rules.json", "w", encoding="utf-8") as f:
                    json.dump(app.rules, f, indent=2)
            return _toggle
        cb = ttk.Checkbutton(list_frame, text=sp, variable=var, command=_make_toggle())
        cb.grid(row=i, column=0, sticky="w")
        app.auto_species_vars[sp] = var


    def on_auto_toggle():
        species = app.selected_species.get()
        if not species:
            show_warning("No species", "Select a species first.")
            app.auto_var.set(False)
            return
        if app.auto_var.get():
            app.mode_vars["automated"].set(True)
        else:
            app.mode_vars["automated"].set(False)
        update_mode_state()

    auto_cb = ttk.Checkbutton(
        app.auto_frame,
        text="Automatic breeding",
        variable=app.auto_var,
        command=on_auto_toggle,
    )
    auto_cb.grid(row=row_auto, column=0, sticky="w", padx=5, pady=2)
    add_tooltip(auto_cb, "Enable automated rule adjustments")

    ttk.Label(app.auto_frame, text="Current females:").grid(row=row_auto, column=1, sticky="e", padx=5)
    count_lbl = ttk.Label(app.auto_frame, textvariable=app.female_count_var)
    count_lbl.grid(row=row_auto, column=2, sticky="w", padx=5)
    row_auto += 1

    ttk.Label(app.auto_frame, text="Stop at females:").grid(row=row_auto, column=0, sticky="e", padx=5)
    stop_spin = ttk.Spinbox(app.auto_frame, textvariable=app.stop_females_var, from_=0, to=999, width=5)
    stop_spin.grid(row=row_auto, column=1, sticky="w", padx=5)
    row_auto += 1

    ttk.Label(app.auto_frame, text="Stop at top-stat females:").grid(row=row_auto, column=0, sticky="e", padx=5)
    stop_top_spin = ttk.Spinbox(app.auto_frame, textvariable=app.stop_top_var, from_=0, to=999, width=5)
    stop_top_spin.grid(row=row_auto, column=1, sticky="w", padx=5)
    row_auto += 1

    # Checkbox vars
    app.mode_vars = {mode: tk.BooleanVar() for mode in DEFAULT_MODES}
    app.stat_vars = {stat: tk.BooleanVar() for stat in ALL_STATS}
    app.mutation_stat_vars = {stat: tk.BooleanVar() for stat in ALL_STATS}

    ttk.Label(app.rules_frame, text="Enabled Modes:", font=FONT).grid(
        row=row_rules, column=0, sticky="nw", padx=5, pady=2
    )
    col = 1
    app.mode_cbs = {}
    for mode in DEFAULT_MODES:
        cb = ttk.Checkbutton(app.rules_frame, text=mode, variable=app.mode_vars[mode])
        cb.grid(row=row_rules, column=col, sticky="w", padx=5, pady=2)
        add_tooltip(cb, f"Enable the {mode} mode for this species")
        app.mode_cbs[mode] = cb
        col += 1

    def update_mode_state():
        disable = app.mode_vars["automated"].get()
        for m, cb in app.mode_cbs.items():
            if m == "automated":
                continue
            cb.configure(state="disabled" if disable else "normal")

    app.mode_cbs["automated"].configure(command=update_mode_state)
    update_mode_state()
    row_rules += 1

    ttk.Label(app.rules_frame, text="Shared Stats (merge/top/war):", font=FONT).grid(
        row=row_rules, column=0, sticky="nw", padx=5, pady=(10, 2)
    )
    sf = ttk.Frame(app.rules_frame)
    sf.grid(row=row_rules, column=1, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = ttk.Checkbutton(sf, text=stat, variable=app.stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=1)
        add_tooltip(cb, f"Track {stat} when merging or rating dinos")
    row_rules += 1

    ttk.Label(app.rules_frame, text="Mutation Stats:", font=FONT).grid(
        row=row_rules, column=0, sticky="nw", padx=5, pady=(10, 2)
    )
    mf = ttk.Frame(app.rules_frame)
    mf.grid(row=row_rules, column=1, columnspan=3, sticky="w")
    for i, stat in enumerate(ALL_STATS):
        cb = ttk.Checkbutton(mf, text=stat, variable=app.mutation_stat_vars[stat])
        cb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=1)
        add_tooltip(cb, f"Monitor mutations affecting {stat}")
    row_rules += 1

    # Optional manual save button (can hide if you don't need it)
    ttk.Button(app.rules_frame, text="Save Species Config", command=lambda: save_species_config(app)).grid(
        row=row_rules, column=0, pady=10
    )
    ttk.Button(app.rules_frame, text="Delete Species", command=lambda: delete_species(app)).grid(
        row=row_rules, column=1, pady=10
    )

    def on_species_select(event):
        new = app.selected_species.get()
        # autosave previous species
        old = app._last_species
        if old:
            rule_modes = [m for m, var in app.mode_vars.items() if var.get()]
            rule_modes.extend(ALWAYS_ON_MODES)
            rule = {
                "modes": rule_modes,
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
    app.auto_var.set("automated" in rule.get("modes", []))
    if s in app.auto_species_vars:
        app.auto_species_vars[s].set(app.auto_var.get())
    count = app.progress.get(s, {}).get("female_count", 0)
    app.female_count_var.set(count)
    app.stop_females_var.set(app.progress.get(s, {}).get("stop_female_count", 0))
    app.stop_top_var.set(app.progress.get(s, {}).get("stop_top_stat_females", 0))
    for stat in ALL_STATS:
        app.stat_vars[stat].set(stat in rule.get("stat_merge_stats", []))
        app.mutation_stat_vars[stat].set(stat in rule.get("mutation_stats", []))
    if hasattr(app, "mode_cbs"):
        # ensure checkbutton states reflect automated setting
        disable = app.mode_vars["automated"].get()
        for m, cb in app.mode_cbs.items():
            if m == "automated":
                continue
            cb.configure(state="disabled" if disable else "normal")


def save_species_config(app):
    s = app.selected_species.get()
    if not s:
        show_warning("No species", "Select a species first.")
        return
    modes = [m for m, var in app.mode_vars.items() if var.get()]
    modes.extend(ALWAYS_ON_MODES)
    app.rules[s] = {
        "modes": modes,
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
