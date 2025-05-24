import json
import os
import tkinter as tk
from tkinter import messagebox

def build_global_tab(app):
    cfg = app.config
    settings = cfg.settings
    row = 0

    # Hotkey
    tk.Label(app.tab_global, text="Hotkey Scan:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    app.hotkey_var = tk.StringVar(value=settings.get("hotkey_scan", "F8"))
    tk.Entry(app.tab_global, textvariable=app.hotkey_var, width=8).grid(row=row, column=1, sticky="w")
    row += 1

    # Delays
    for key, label in [
        ("popup_delay", "Popup Delay (s):"),
        ("action_delay", "Action Delay (s):"),
        ("scan_loop_delay", "Scan Loop Delay (s):")
    ]:
        tk.Label(app.tab_global, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        var = tk.DoubleVar(value=settings.get(key, 0.25))
        setattr(app, f"{key}_var", var)
        tk.Entry(app.tab_global, textvariable=var, width=8).grid(row=row, column=1, sticky="w")
        row += 1

    # Log levels
    tk.Label(app.tab_global, text="Log Levels (per module):").grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(10,0))
    row += 1

    modules = ["scanner", "ocr_helpers", "tracker", "logic", "gui"]
    app.log_level_vars = {}
    for mod in modules:
        tk.Label(app.tab_global, text=f"{mod}:").grid(row=row, column=0, sticky="w", padx=5)
        var = tk.StringVar(value=settings.get("log_levels", {}).get(mod, "INFO"))
        app.log_level_vars[mod] = var
        tk.OptionMenu(app.tab_global, var, "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG").grid(row=row, column=1, sticky="w")
        row += 1

    def save_globals():
        settings["hotkey_scan"] = app.hotkey_var.get()
        settings["popup_delay"] = app.popup_delay_var.get()
        settings["action_delay"] = app.action_delay_var.get()
        settings["scan_loop_delay"] = app.scan_loop_delay_var.get()
        settings["log_levels"] = {m: v.get() for m, v in app.log_level_vars.items()}

        with open(cfg.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        messagebox.showinfo("Saved", "Global settings saved.")

    tk.Button(app.tab_global, text="Save Global Settings", command=save_globals) \
      .grid(row=row, column=0, columnspan=2, pady=10)
