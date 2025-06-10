import tkinter as tk
from tkinter import ttk


def refresh_species_dropdown(app):
    """Reload progress for the current wipe and refresh the species combobox."""
    from progress_tracker import load_progress

    if hasattr(app, "settings"):
        app.progress = load_progress(app.settings.get("current_wipe", "default"))

    if hasattr(app, "species_dropdown"):
        app.species_dropdown["values"] = sorted(app.progress.keys())


def add_tooltip(widget, text: str) -> None:
    """Attach a simple tooltip to ``widget`` displaying ``text``."""

    tip = tk.Toplevel(widget)
    tip.wm_overrideredirect(True)
    tip.withdraw()
    lbl = ttk.Label(tip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
    lbl.pack(ipadx=2, ipady=1)

    def show(_):
        x = widget.winfo_rootx() + 20
        y = widget.winfo_rooty() + widget.winfo_height() + 5
        tip.wm_geometry(f"+{x}+{y}")
        tip.deiconify()

    def hide(_):
        tip.withdraw()

    widget.bind("<Enter>", show)
    widget.bind("<Leave>", hide)
