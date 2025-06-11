import json
import os
import tkinter as tk
from tkinter import ttk

from progress_tracker import load_progress
from stat_list import generate_stat_list

FONT = ("Segoe UI", 10)


def build_stat_list_tab(app):
    row = 0
    app.stat_list_box = tk.Text(app.tab_stat_list, height=10, width=50, state="disabled")
    app.stat_list_box.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
    row += 1

    ttk.Button(app.tab_stat_list, text="Refresh", command=lambda: refresh_list()).grid(row=row, column=0, sticky="w", padx=5)
    row += 1

    ttk.Label(app.tab_stat_list, text="Add Custom Line:", font=FONT).grid(row=row, column=0, sticky="w", padx=5)
    app.custom_line_var = tk.StringVar()
    entry = ttk.Entry(app.tab_stat_list, textvariable=app.custom_line_var, width=30)
    entry.grid(row=row, column=1, sticky="w")
    ttk.Button(app.tab_stat_list, text="Add", command=lambda: add_custom_line()).grid(row=row, column=2, sticky="w")
    row += 1

    app.custom_lines_list = tk.Listbox(app.tab_stat_list, height=4, width=50)
    app.custom_lines_list.grid(row=row, column=0, columnspan=3, padx=5, pady=2, sticky="nsew")
    row += 1
    ttk.Button(app.tab_stat_list, text="Delete Selected", command=lambda: delete_custom_line()).grid(row=row, column=0, sticky="w", padx=5)
    row += 1

    def refresh_list(event=None):
        progress = load_progress(app.settings.get("current_wipe", "default"))
        rules = {}
        if app.settings.get("stat_list_mode") == "mutation" and os.path.exists("rules.json"):
            with open("rules.json", "r", encoding="utf-8") as f:
                rules = json.load(f)
        lines = generate_stat_list(progress, rules, app.settings)
        app.stat_list_box.configure(state="normal")
        app.stat_list_box.delete("1.0", "end")
        app.stat_list_box.insert("end", "\n".join(lines))
        app.stat_list_box.configure(state="disabled")

        app.custom_lines_list.delete(0, "end")
        for line in app.settings.get("custom_stat_list_lines", []):
            app.custom_lines_list.insert("end", line)

    def add_custom_line():
        line = app.custom_line_var.get().strip()
        if not line:
            return
        app.settings.setdefault("custom_stat_list_lines", []).append(line)
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(app.settings, f, indent=2)
        app.custom_line_var.set("")
        refresh_list()

    def delete_custom_line():
        sel = app.custom_lines_list.curselection()
        if not sel:
            return
        idx = sel[0]
        lines = app.settings.get("custom_stat_list_lines", [])
        if 0 <= idx < len(lines):
            del lines[idx]
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(app.settings, f, indent=2)
        refresh_list()

    refresh_list()
