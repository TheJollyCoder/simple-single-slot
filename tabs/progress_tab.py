import tkinter as tk
from tkinter import ttk
from utils.dialogs import show_error, show_warning, show_info
import json
from progress_tracker import load_progress

FONT = ("Segoe UI", 10)


def build_stats_tab(app):
    row = 0
    ttk.Label(app.tab_stats, text="Select Species:", font=FONT).grid(row=row, column=0, sticky="w", padx=5, pady=2)
    app.progress_species = tk.StringVar()
    species = list(load_progress(app.settings.get("current_wipe", "default")).keys())
    app.progress_dropdown = ttk.Combobox(app.tab_stats, values=species, textvariable=app.progress_species, state="readonly", width=30)
    app.progress_dropdown.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    # placeholder for potential future info
    row += 1


    app.stat_list_text = tk.Text(app.tab_stats, height=6, width=50, state="disabled")
    app.stat_list_text.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
    row += 1

    ttk.Label(app.tab_stats, text="Add Custom Line:", font=FONT).grid(row=row, column=0, sticky="w", padx=5)
    app.custom_line_var = tk.StringVar()
    entry = ttk.Entry(app.tab_stats, textvariable=app.custom_line_var, width=30)
    entry.grid(row=row, column=1, sticky="w")
    ttk.Button(app.tab_stats, text="Add", command=lambda: add_custom_line()).grid(row=row, column=2, sticky="w")
    row += 1

    app.custom_lines_list = tk.Listbox(app.tab_stats, height=4, width=50)
    app.custom_lines_list.grid(row=row, column=0, columnspan=3, padx=5, pady=2, sticky="nsew")
    row += 1
    ttk.Button(app.tab_stats, text="Delete Selected", command=lambda: delete_custom_line()).grid(row=row, column=0, sticky="w", padx=5)
    row += 1

    def refresh_tables(event=None):
        prog = load_progress(app.settings.get("current_wipe", "default"))
        sp = app.progress_species.get()

        lines = []
        if sp:
            data = prog.get(sp, {})
            lines.append(f"{sp} stud stats:")
            stud = data.get("stud", {})
            if stud:
                lines.append("Main Stud:")
                for st, val in stud.items():
                    lines.append(f"  {st}: {val}")
            mstud = data.get("mutation_stud", {})
            if mstud:
                lines.append("Mutation Stud:")
                for st, val in mstud.items():
                    lines.append(f"  {st}: {val}")

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
        prog = load_progress(app.settings.get("current_wipe", "default"))
        data = prog.get(sp, {})
        lines = [f"{sp} stud stats:"]
        stud = data.get("stud", {})
        if stud:
            lines.append("Main Stud:")
            for st, val in stud.items():
                lines.append(f"  {st}: {val}")
        mstud = data.get("mutation_stud", {})
        if mstud:
            lines.append("Mutation Stud:")
            for st, val in mstud.items():
                lines.append(f"  {st}: {val}")
        msg = "\n".join(lines)
        app.clipboard_clear()
        app.clipboard_append(msg)
        try:
            from discord_bot import send_progress_message
            send_progress_message(msg)
            show_info("Sent", "Stats sent to Discord and copied to clipboard.")
        except Exception as e:
            show_error("Error", str(e))

    btn_frame = ttk.Frame(app.tab_stats)
    btn_frame.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="w")
    ttk.Button(btn_frame, text="Copy/Send Stats", command=send_summary).pack(side="left")
    ttk.Button(btn_frame, text="Refresh", command=refresh_tables).pack(side="left", padx=5)

    refresh_tables()
