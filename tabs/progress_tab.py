import tkinter as tk
from tkinter import ttk
from utils.dialogs import show_error, show_warning, show_info
import time
import json
from progress_tracker import load_progress, load_history

FONT = ("Segoe UI", 10)
ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]


def build_progress_tab(app):
    row = 0
    ttk.Label(app.tab_progress, text="Select Species:", font=FONT).grid(row=row, column=0, sticky="w", padx=5, pady=2)
    app.progress_species = tk.StringVar()
    species = list(load_progress().keys())
    app.progress_dropdown = ttk.Combobox(app.tab_progress, values=species, textvariable=app.progress_species, state="readonly", width=30)
    app.progress_dropdown.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    cols = ("Stat", "Top", "Threshold")
    app.progress_tree = ttk.Treeview(app.tab_progress, columns=cols, show="headings", height=6)
    for c in cols:
        app.progress_tree.heading(c, text=c)
        app.progress_tree.column(c, width=90)
    app.progress_tree.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
    row += 1

    hist_cols = ("Time", "Stat", "Value", "Type")
    app.history_tree = ttk.Treeview(app.tab_progress, columns=hist_cols, show="headings", height=8)
    for c in hist_cols:
        app.history_tree.heading(c, text=c)
        app.history_tree.column(c, width=100)
    app.history_tree.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
    row += 1

    def refresh_tables(event=None):
        prog = load_progress()
        hist = load_history()
        sp = app.progress_species.get()
        for i in app.progress_tree.get_children():
            app.progress_tree.delete(i)
        for st in ALL_STATS:
            top = prog.get(sp, {}).get("top_stats", {}).get(st, "")
            thr = prog.get(sp, {}).get("mutation_thresholds", {}).get(st, "")
            app.progress_tree.insert("", "end", values=(st, top, thr))
        for i in app.history_tree.get_children():
            app.history_tree.delete(i)
        sp_hist = hist.get(sp, {})
        for cat in ["top_stats", "mutation_thresholds"]:
            for st, logs in sp_hist.get(cat, {}).items():
                for entry in logs:
                    ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(entry.get("ts", 0)))
                    val = entry.get("value")
                    app.history_tree.insert("", "end", values=(ts, st, val, "top" if cat == "top_stats" else "threshold"))

    app.progress_dropdown.bind("<<ComboboxSelected>>", refresh_tables)

    def send_summary():
        sp = app.progress_species.get()
        if not sp:
            show_warning("No species", "Select a species first.")
            return
        prog = load_progress().get(sp, {})
        lines = [f"{sp} stats:"]
        lines.append("Top Stats:")
        for st, val in prog.get("top_stats", {}).items():
            lines.append(f"  {st}: {val}")
        lines.append("Mutation Thresholds:")
        for st, val in prog.get("mutation_thresholds", {}).items():
            lines.append(f"  {st}: {val}")
        msg = "\n".join(lines)
        app.clipboard_clear()
        app.clipboard_append(msg)
        url = app.settings.get("webhook_url", "")
        if url:
            try:
                import urllib.request
                req = urllib.request.Request(url, data=json.dumps({"content": msg}).encode("utf-8"), headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req)
                show_info("Sent", "Summary sent to Discord and copied to clipboard.")
            except Exception as e:
                show_error("Error", str(e))
        else:
            show_info("Copied", "Summary copied to clipboard.")

    ttk.Button(app.tab_progress, text="Copy/Send Summary", command=send_summary).grid(row=row, column=0, padx=5, pady=5, sticky="w")
