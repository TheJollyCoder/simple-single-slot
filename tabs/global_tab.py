import tkinter as tk
from tkinter import ttk
from utils.dialogs import show_info

from utils.helpers import add_tooltip

FONT = ("Segoe UI", 10)

def build_global_tab(app):
    row = 0
    ttk.Label(app.tab_global, text="Hotkey Scan", font=FONT).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    app.hotkey_var = tk.StringVar(value=app.settings.get("hotkey_scan", "F8"))
    entry = ttk.Entry(app.tab_global, textvariable=app.hotkey_var, width=10)
    entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    add_tooltip(entry, "Keyboard hotkey to start live scanning")
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
        add_tooltip(spin, f"{label} in seconds")
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
        add_tooltip(cb, f"Enable debug logs for {mod}")
        row += 1

    def save_all():
        app.settings["hotkey_scan"] = app.hotkey_var.get()
        app.settings["popup_delay"] = app.popup_delay_var.get()
        app.settings["action_delay"] = app.action_delay_var.get()
        app.settings["scan_loop_delay"] = app.scan_loop_delay_var.get()
        app.settings["debug_mode"] = {k: v.get() for k, v in app.debug_vars.items()}
        with open("settings.json", "w", encoding="utf-8") as f:
            import json
            json.dump(app.settings, f, indent=2)
        show_info("Saved", "Global settings saved.")
        if hasattr(app, "update_hotkeys"):
            app.update_hotkeys()

    ttk.Button(app.tab_global, text="Save Settings", command=save_all).grid(
        row=row, column=0, columnspan=2, pady=10
    )
