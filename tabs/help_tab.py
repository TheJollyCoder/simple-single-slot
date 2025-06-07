import tkinter as tk
from tkinter import ttk

HELP_TEXT = (
    "1. Use 'Run Calibration' on the Tools tab to set screen positions.\n"
    "2. Configure global options and delays in Global Settings.\n"
    "3. Define per-species rules on the Species Config tab.\n"
    "4. Press the configured hotkey or click Start to begin scanning.\n"
    "5. Script Control provides manual tests and logs."
)

def build_help_tab(app):
    lbl = ttk.Label(app.tab_help, text=HELP_TEXT, justify="left", wraplength=700)
    lbl.pack(padx=10, pady=10, anchor="nw")

