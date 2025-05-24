import os
import threading
import time
import tkinter as tk
from tkinter import ttk

import keyboard

from config.config import Config
from scan.scanner import scan_slot, input_queue
from tracking.progress_tracker import ProgressTracker
from logic.breeding_logic import should_keep_egg
from utils.logger import get_logger

from .global_tab import GlobalTab
from .species_tab import SpeciesTab
from .tools_tab import ToolsTab
from .test_tab import TestTab

log = get_logger("gui")

class SettingsEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ark Breeding Settings Editor")
        self.geometry("900x600")

        # Initialize configuration and progress tracker
        config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
        self.config = Config(config_dir)
        self.tracker = ProgressTracker(self.config)
        self.live_running = False

        # Create tabbed interface
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.global_tab  = GlobalTab(self.notebook, self.config)
        self.species_tab = SpeciesTab(self.notebook, self.config)
        self.tools_tab   = ToolsTab(self.notebook, self.config)
        self.test_tab    = TestTab(self.notebook, self.config)

        self.notebook.add(self.global_tab,  text="Global Settings")
        self.notebook.add(self.species_tab, text="Species Config")
        self.notebook.add(self.tools_tab,   text="Tools & Defaults")
        self.notebook.add(self.test_tab,    text="Test Control")

        # Hotkeys for live scanning
        keyboard.add_hotkey("F8", self.toggle_live)
        keyboard.add_hotkey("F9", self.pause_live)

    def toggle_live(self):
        if not self.live_running:
            self.live_running = True
            threading.Thread(target=self.run_loop, daemon=True).start()
        else:
            self.live_running = False

    def pause_live(self):
        self.live_running = False

    def run_loop(self):
        while self.live_running:
            try:
                slot = scan_slot(self.config)
                if slot != "no_egg":
                    sp  = slot["species"]
                    sex = "male" if "male" in sp.lower() else "female"
                    keep, reasons = should_keep_egg(slot, sp, sex, self.config)

                    x, y = (self.config.settings["slot_x"], self.config.settings["slot_y"])
                    if keep:
                        input_queue.put(("double_click", (x, y)))
                        self.tracker.update_top_stats(sp, slot["stats"])
                        self.tracker.update_mutation_thresholds(sp, slot["stats"], sex)
                        self.tracker.update_stud(sp, slot["stats"], sex)
                    else:
                        input_queue.put(("right_click", (x, y)))

                    self.tracker.save()

                time.sleep(self.config.settings.get("scan_interval", 0.5))
            except Exception:
                log.exception("Live-scan loop error")
                break

if __name__ == "__main__":
    app = SettingsEditor()
    app.mainloop()
