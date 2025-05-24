import json
import tkinter as tk
from tkinter import messagebox

from utils.logger import get_logger

log = get_logger("global_tab")

class GlobalTab(tk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        s = config.settings

        # Numeric settings
        labels = [
            ("Slot X",       "slot_x"),
            ("Slot Y",       "slot_y"),
            ("Popup Delay",  "popup_delay"),
            ("Action Delay", "action_delay"),
            ("Scan Interval","scan_interval"),
        ]
        self.entries = {}
        for i, (text, key) in enumerate(labels):
            tk.Label(self, text=text).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            e = tk.Entry(self)
            e.grid(row=i, column=1, sticky="ew", padx=5)
            e.insert(0, str(s.get(key, "")))
            self.entries[key] = e

        # OCR settings
        row = len(labels)
        tk.Label(self, text="OCR PSM").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.psm = tk.Entry(self)
        self.psm.grid(row=row, column=1, sticky="ew", padx=5)
        self.psm.insert(0, str(s.get("ocr", {}).get("psm", "")))

        row += 1
        tk.Label(self, text="OCR OEM").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.oem = tk.Entry(self)
        self.oem.grid(row=row, column=1, sticky="ew", padx=5)
        self.oem.insert(0, str(s.get("ocr", {}).get("oem", "")))

        # Log levels
        row += 1
        tk.Label(self, text="Log Levels (module:level)").grid(row=row, column=0, sticky="nw", padx=5, pady=2)
        self.log_text = tk.Text(self, height=4)
        self.log_text.grid(row=row, column=1, sticky="ew", padx=5)
        for mod, lvl in s.get("log_levels", {}).items():
            self.log_text.insert("end", f"{mod}:{lvl}\n")

        # Save button
        row += 1
        tk.Button(self, text="Save Global Settings", command=self.save).grid(
            row=row, column=0, columnspan=2, pady=10
        )

        self.columnconfigure(1, weight=1)

    def save(self):
        # Numeric values
        for key, e in self.entries.items():
            val = e.get().strip()
            try:
                self.config.settings[key] = float(val) if "." in val else int(val)
            except ValueError:
                self.config.settings[key] = val

        # OCR values
        try:
            self.config.settings.setdefault("ocr", {})["psm"] = int(self.psm.get().strip())
            self.config.settings.setdefault("ocr", {})["oem"] = int(self.oem.get().strip())
        except ValueError:
            log.error("Invalid OCR setting", exc_info=True)

        # Log levels
        log_lv = {}
        for line in self.log_text.get("1.0", "end").strip().splitlines():
            if ":" in line:
                mod, lvl = line.split(":", 1)
                log_lv[mod.strip()] = lvl.strip()
        self.config.settings["log_levels"] = log_lv

        # Write back to file
        try:
            with open(self.config.settings_path, "w", encoding="utf-8") as f:
                json.dump(self.config.settings, f, indent=2)
            messagebox.showinfo("Saved", "Global settings saved.")
        except Exception:
            log.exception("Failed to save global settings")
            messagebox.showerror("Error", "Could not save settings.")
