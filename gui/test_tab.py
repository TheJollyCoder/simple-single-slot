import tkinter as tk
from tkinter import scrolledtext
import threading
import time

from scan.scanner import scan_slot

def build_test_tab(app):
    frame = app.tab_test
    row = 0

    tk.Button(frame, text="Test Single Scan",
              command=lambda: threading.Thread(target=_test_single, args=(app,), daemon=True).start()) \
      .grid(row=row, column=0, padx=5, pady=5)
    tk.Button(frame, text="Test Multi Scan (×5)",
              command=lambda: threading.Thread(target=_test_multi, args=(app,), daemon=True).start()) \
      .grid(row=row, column=1, padx=5, pady=5)
    row += 1

    text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=20)
    text.grid(row=row, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
    frame.grid_rowconfigure(row, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    app.test_output = text

def _test_single(app):
    app.test_output.delete(1.0, tk.END)
    app.test_output.insert(tk.END, "→ Running single scan...\n")
    try:
        result = scan_slot(app.config)
        app.test_output.insert(tk.END, f"{result}\n")
    except Exception as e:
        app.test_output.insert(tk.END, f"Error: {e}\n")

def _test_multi(app):
    app.test_output.delete(1.0, tk.END)
    app.test_output.insert(tk.END, "→ Running 5 scans...\n")
    for i in range(5):
        try:
            result = scan_slot(app.config)
            app.test_output.insert(tk.END, f"{i+1}: {result}\n")
        except Exception as e:
            app.test_output.insert(tk.END, f"Error on scan {i+1}: {e}\n")
        time.sleep(app.config.settings.get("scan_loop_delay", 0.5))
