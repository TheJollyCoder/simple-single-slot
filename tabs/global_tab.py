import tkinter as tk

def build_global_tab(app):
    row = 0
    tk.Label(app.tab_global, text="Hotkey Scan").grid(row=row, column=0, sticky="w")
    app.hotkey_var = tk.StringVar(value=app.settings.get("hotkey_scan", "F8"))
    tk.Entry(app.tab_global, textvariable=app.hotkey_var).grid(row=row, column=1, sticky="w")
    row += 1

    for delay_key in ["popup_delay", "action_delay", "scan_loop_delay"]:
        tk.Label(app.tab_global, text=delay_key).grid(row=row, column=0, sticky="w")
        var = tk.DoubleVar(value=app.settings.get(delay_key, 0.25))
        setattr(app, f"{delay_key}_var", var)
        tk.Spinbox(app.tab_global, textvariable=var, from_=0.0, to=5.0, increment=0.05, width=6).grid(row=row, column=1, sticky="w")
        row += 1

    tk.Label(app.tab_global, text="Per-Module Debug:").grid(row=row, column=0, sticky="w")
    row += 1

    debug_config = app.settings.get("debug_mode", {})
    if isinstance(debug_config, bool):
        debug_config = {k: debug_config for k in ["scanner", "scan_eggs", "progress_tracker", "breeding_logic"]}
    app.debug_vars = {}
    for mod in ["scanner", "scan_eggs", "progress_tracker", "breeding_logic"]:
        var = tk.BooleanVar(value=debug_config.get(mod, False))
        app.debug_vars[mod] = var
        tk.Checkbutton(app.tab_global, text=mod, variable=var).grid(row=row, column=1, sticky="w")
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
        tk.messagebox.showinfo("Saved", "Global settings saved.")
        if hasattr(app, "update_hotkeys"):
            app.update_hotkeys()

    tk.Button(app.tab_global, text="Save Settings", command=save_all).grid(row=row, column=0, pady=10)
