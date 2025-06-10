import tkinter as tk
from tkinter import ttk
from utils.dialogs import show_error, show_warning, show_info
import json
from progress_tracker import load_progress
from stat_list import generate_stat_list, EXTRA_TAMES_FILE

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


    app.stat_list_text = tk.Text(app.tab_progress, height=6, width=50, state="disabled")
    app.stat_list_text.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
    row += 1

    ttk.Label(app.tab_progress, text="Custom Entry:", font=FONT).grid(row=row, column=0, sticky="w", padx=5, pady=2)
    app.custom_entry_var = tk.StringVar()
    ttk.Entry(app.tab_progress, textvariable=app.custom_entry_var, width=20).grid(row=row, column=1, sticky="w", padx=5, pady=2)

    btn_custom = ttk.Frame(app.tab_progress)
    btn_custom.grid(row=row, column=2, sticky="w")
    row += 1

    def add_custom_entry():
        sp = app.custom_entry_var.get().strip()
        if not sp:
            show_warning("No species", "Enter a species name.")
            return
        try:
            with open(EXTRA_TAMES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        if sp in data:
            show_warning("Exists", f"{sp} already exists.")
            return
        data[sp] = {"stud": {}, "mutation_thresholds": {}}
        with open(EXTRA_TAMES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        app.custom_entry_var.set("")
        refresh_tables()

    def remove_custom_entry():
        sp = app.custom_entry_var.get().strip()
        if not sp:
            show_warning("No species", "Enter a species name.")
            return
        try:
            with open(EXTRA_TAMES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        if sp not in data:
            show_warning("Missing", f"{sp} not found.")
            return
        data.pop(sp, None)
        with open(EXTRA_TAMES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        app.custom_entry_var.set("")
        refresh_tables()

    ttk.Button(btn_custom, text="Add", command=add_custom_entry).pack(side="left")
    ttk.Button(btn_custom, text="Remove", command=remove_custom_entry).pack(side="left", padx=5)

    def refresh_tables(event=None):
        prog = load_progress(app.settings.get("current_wipe", "default"))
        sp = app.progress_species.get()
        count = prog.get(sp, {}).get("female_count", 0)
        app.female_count_var.set(f"Females: {count}")

        lines = generate_stat_list(prog, app.rules, app.settings)
        app.stat_list_text.configure(state="normal")
        app.stat_list_text.delete("1.0", "end")
        app.stat_list_text.insert("end", "\n".join(lines))
        app.stat_list_text.configure(state="disabled")

    app.progress_dropdown.bind("<<ComboboxSelected>>", refresh_tables)

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
