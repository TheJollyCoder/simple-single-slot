import tkinter as tk
from tkinter import ttk
from progress_tracker import ensure_wipe_dir, load_progress
import os

from utils.helpers import add_tooltip, refresh_species_dropdown

FONT = ("Segoe UI", 10)

def build_global_tab(app):
    row = 0
    ttk.Label(app.tab_global, text="Current Wipe", font=FONT).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    existing = []
    if os.path.isdir("wipes"):
        existing = sorted(d for d in os.listdir("wipes") if os.path.isdir(os.path.join("wipes", d)))
    app.wipe_var = tk.StringVar(value=app.settings.get("current_wipe", "default"))
    wipe_combo = ttk.Combobox(
        app.tab_global,
        textvariable=app.wipe_var,
        values=existing,
        width=12,
    )
    wipe_combo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    add_tooltip(wipe_combo, "Select or enter wipe name")

    def on_wipe_change(_=None):
        app.settings["current_wipe"] = app.wipe_var.get() or "default"
        ensure_wipe_dir(app.settings["current_wipe"])
        app.progress = load_progress(app.settings["current_wipe"])
        refresh_species_dropdown(app)

    wipe_combo.bind("<<ComboboxSelected>>", on_wipe_change)
    wipe_combo.bind("<Return>", on_wipe_change)
    wipe_combo.bind("<FocusOut>", on_wipe_change)
    row += 1
    ttk.Label(app.tab_global, text="Hotkey Scan", font=FONT).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    app.hotkey_var = tk.StringVar(value=app.settings.get("hotkey_scan", "F8"))
    entry = ttk.Entry(app.tab_global, textvariable=app.hotkey_var, width=10)
    entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    add_tooltip(entry, "Keyboard key that triggers the live scan loop")
    row += 1

    for delay_key in ["popup_delay", "action_delay", "scan_loop_delay"]:
        label = delay_key.replace("_", " ").title()
        ttk.Label(app.tab_global, text=label, font=FONT).grid(
            row=row, column=0, sticky="w", padx=5, pady=2
        )
        var = tk.DoubleVar(value=app.settings.get(delay_key, 0.25))
        setattr(app, f"{delay_key}_var", var)
        spin = ttk.Spinbox(
            app.tab_global,
            textvariable=var,
            from_=0.0,
            to=5.0,
            increment=0.05,
            width=8,
        )
        spin.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        tip_map = {
            "Popup Delay": "Time to wait after clicking before reading the popup",
            "Action Delay": "Interval between automated mouse actions",
            "Scan Loop Delay": "Pause between each scan cycle",
        }
        add_tooltip(spin, tip_map.get(label, f"{label} in seconds"))
        row += 1


    app.auto_eat_var = tk.BooleanVar(value=app.settings.get("auto_eat_enabled", False))
    cb_auto = ttk.Checkbutton(app.tab_global, text="Enable Auto-Eat", variable=app.auto_eat_var)
    cb_auto.grid(row=row, column=2, sticky="w", padx=5, pady=2)
    add_tooltip(cb_auto, "Automatically consume food periodically")
    row += 1

    app.monitored_scan_var = tk.BooleanVar(value=app.settings.get("monitored_scan", True))
    cb_mon = ttk.Checkbutton(app.tab_global, text="Monitored Scan", variable=app.monitored_scan_var)
    cb_mon.grid(row=row, column=2, sticky="w", padx=5, pady=2)
    add_tooltip(cb_mon, "Pause on unknown species to configure rules")
    row += 1

    ttk.Label(app.tab_global, text="Per-Module Debug:", font=FONT).grid(
        row=row, column=0, sticky="w", padx=5, pady=(10, 2)
    )
    row += 1

    debug_config = app.settings.get("debug_mode", {})
    if isinstance(debug_config, bool):
        debug_config = {
            k: debug_config
            for k in ["scanner", "scan_eggs", "progress_tracker", "breeding_logic"]
        }
    app.debug_vars = {}
    for mod in ["scanner", "scan_eggs", "progress_tracker", "breeding_logic"]:
        var = tk.BooleanVar(value=debug_config.get(mod, False))
        app.debug_vars[mod] = var
        cb = ttk.Checkbutton(app.tab_global, text=mod, variable=var)
        cb.grid(row=row, column=1, sticky="w", padx=5, pady=1)
        add_tooltip(cb, f"Print detailed logs from the {mod} module")
        row += 1

    def save_all():
        app.settings["hotkey_scan"] = app.hotkey_var.get()
        app.settings["popup_delay"] = app.popup_delay_var.get()
        app.settings["action_delay"] = app.action_delay_var.get()
        app.settings["scan_loop_delay"] = app.scan_loop_delay_var.get()
        app.settings["auto_eat_enabled"] = app.auto_eat_var.get()
        app.settings["monitored_scan"] = app.monitored_scan_var.get()
        app.settings["debug_mode"] = {k: v.get() for k, v in app.debug_vars.items()}
        app.settings["current_wipe"] = app.wipe_var.get() or "default"
        ensure_wipe_dir(app.settings["current_wipe"])
        app.progress = load_progress(app.settings["current_wipe"])
        refresh_species_dropdown(app)
        with open("settings.json", "w", encoding="utf-8") as f:
            import json
            json.dump(app.settings, f, indent=2)
        try:
            import importlib, logger, scanner, breeding_logic, progress_tracker
            importlib.reload(logger)
            scanner.log = logger.get_logger("scanner")
            breeding_logic.log = logger.get_logger("breeding_logic")
            breeding_logic.kept_log = logger.get_logger("kept_eggs")
            breeding_logic.destroyed_log = logger.get_logger("destroyed_eggs")
            progress_tracker.log = logger.get_logger("progress_tracker")
        except Exception:
            pass
        if hasattr(app, "update_hotkeys"):
            app.update_hotkeys()
        if hasattr(app, "flash_status"):
            app.flash_status("Saved")

    ttk.Button(app.tab_global, text="Save Settings", command=save_all).grid(
        row=row, column=0, columnspan=3, pady=10
    )
