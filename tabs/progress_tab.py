import tkinter as tk
from tkinter import ttk
from utils.dialogs import show_error, show_warning, show_info
import time
import json
from progress_tracker import load_progress, load_history
from stat_list import generate_stat_list

FONT = ("Segoe UI", 10)
ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]


def build_progress_tab(app):
    row = 0
    ttk.Label(app.tab_progress, text="Select Species:", font=FONT).grid(row=row, column=0, sticky="w", padx=5, pady=2)
    app.progress_species = tk.StringVar()
    species = list(load_progress(app.settings.get("current_wipe", "default")).keys())
    app.progress_dropdown = ttk.Combobox(app.tab_progress, values=species, textvariable=app.progress_species, state="readonly", width=30)
    app.progress_dropdown.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    app.female_count_var = tk.StringVar()
    ttk.Label(app.tab_progress, textvariable=app.female_count_var, font=FONT).grid(row=row, column=2, sticky="w", padx=5, pady=2)
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

    app.stat_list_text = tk.Text(app.tab_progress, height=6, width=50, state="disabled")
    app.stat_list_text.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
    row += 1

    ttk.Label(app.tab_progress, text="Add Custom Line:", font=FONT).grid(row=row, column=0, sticky="w", padx=5)
    app.custom_line_var = tk.StringVar()
    entry = ttk.Entry(app.tab_progress, textvariable=app.custom_line_var, width=30)
    entry.grid(row=row, column=1, sticky="w")
    ttk.Button(app.tab_progress, text="Add", command=lambda: add_custom_line()).grid(row=row, column=2, sticky="w")
    row += 1

    app.custom_lines_list = tk.Listbox(app.tab_progress, height=4, width=50)
    app.custom_lines_list.grid(row=row, column=0, columnspan=3, padx=5, pady=2, sticky="nsew")
    row += 1
    ttk.Button(app.tab_progress, text="Delete Selected", command=lambda: delete_custom_line()).grid(row=row, column=0, sticky="w", padx=5)
    row += 1

    def refresh_tables(event=None):
        prog = load_progress(app.settings.get("current_wipe", "default"))
        hist = load_history(app.settings.get("current_wipe", "default"))
        sp = app.progress_species.get()
        count = prog.get(sp, {}).get("female_count", 0)
        app.female_count_var.set(f"Females: {count}")
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

        lines = generate_stat_list(prog, app.rules, app.settings)
        app.stat_list_text.configure(state="normal")
        app.stat_list_text.delete("1.0", "end")
        app.stat_list_text.insert("end", "\n".join(lines))
        app.stat_list_text.configure(state="disabled")

        app.custom_lines_list.delete(0, "end")
        for line in app.settings.get("custom_stat_list_lines", []):
            app.custom_lines_list.insert("end", line)

    app.progress_dropdown.bind("<<ComboboxSelected>>", refresh_tables)

    def add_custom_line():
        line = app.custom_line_var.get().strip()
        if not line:
            return
        app.settings.setdefault("custom_stat_list_lines", []).append(line)
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(app.settings, f, indent=2)
        app.custom_line_var.set("")
        refresh_tables()

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
        refresh_tables()

    def send_summary():
        sp = app.progress_species.get()
        if not sp:
            show_warning("No species", "Select a species first.")
            return
        prog = load_progress(app.settings.get("current_wipe", "default")).get(sp, {})
        lines = [f"{sp} stats:"]
        lines.append(f"Females: {prog.get('female_count', 0)}")
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

    btn_frame = ttk.Frame(app.tab_progress)
    btn_frame.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="w")
    ttk.Button(btn_frame, text="Copy/Send Summary", command=send_summary).pack(side="left")
    ttk.Button(btn_frame, text="Refresh", command=refresh_tables).pack(side="left", padx=5)

    refresh_tables()
