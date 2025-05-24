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

from gui.global_tab import build_global_tab
from gui.species_tab import build_species_tab
from gui.tools_tab import build_tools_tab
from gui.test_tab import build_test_tab

log = get_logger("gui")

class SettingsEditor(tk.Tk):
    ALL_MODES = ["mutations", "all_females", "stat_merge", "top_stat_females", "war"]
    ALL_STATS = ["health", "stamina", "weight", "melee", "oxygen", "food"]

    def __init__(self):
        super().__init__()
        self.title("ARK Breeding Config Editor")
        self.geometry("800x600")

        # point Config at the config/ directory
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(repo_root, "config")
        self.config = Config(config_dir)
        self.tracker = ProgressTracker(self.config)

        # state flags
        self.live_running = False
        self.scanning_paused = False

        # prepare per-species UI vars
        self.mode_vars = {mode: tk.BooleanVar() for mode in self.ALL_MODES}
        self.mut_stat_vars = {stat: tk.BooleanVar() for stat in self.ALL_STATS}
        self.top_stat_vars = {stat: tk.BooleanVar() for stat in self.ALL_STATS}

        # build the tabbed interface
        self.create_tabs()

        # hotkeys
        keyboard.add_hotkey(self.config.settings.get("hotkey_scan", "F8"), self.toggle_live)
        keyboard.add_hotkey("F9", self.toggle_pause)
        keyboard.add_hotkey("escape", self.quit_app)

    def create_tabs(self):
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill=tk.BOTH)

        self.tab_global  = ttk.Frame(notebook); notebook.add(self.tab_global,  text="Global Settings")
        self.tab_species = ttk.Frame(notebook); notebook.add(self.tab_species, text="Species Config")
        self.tab_tools   = ttk.Frame(notebook); notebook.add(self.tab_tools,   text="Defaults & Tools")
        self.tab_test    = ttk.Frame(notebook); notebook.add(self.tab_test,    text="Script Control")

        build_global_tab(self)
        build_species_tab(self)
        build_tools_tab(self)
        build_test_tab(self)

    def toggle_live(self):
        if not self.live_running:
            self.live_running = True
            threading.Thread(target=self.run_loop, daemon=True).start()
            log.info("▶️ Live scanning started")
        else:
            self.live_running = False
            log.info("⏹ Live scanning stopped")

    def run_loop(self):
        while self.live_running:
            if getattr(self, "scanning_paused", False):
                time.sleep(0.1)
                continue
            try:
                result = scan_slot(self.config)
                if result == "no_egg":
                    time.sleep(self.config.settings.get("scan_loop_delay", 0.5))
                    continue

                species_raw = result["species"]
                stats       = result["stats"]
                sex         = "female" if "female" in species_raw.lower() else "male"
                species     = self.tracker.normalize_species(species_raw)

                keep, reasons = should_keep_egg(result, species, sex, self.config)
                x, y = self.config.settings["slot_x"], self.config.settings["slot_y"]

                if keep:
                    input_queue.put(("double_click", (x, y)))
                    log.info(f"✔ Kept egg: {species_raw}")
                    self.tracker.update_top_stats(species, stats)
                    self.tracker.update_mutation_thresholds(species, stats, sex)
                    self.tracker.update_stud(species, stats, sex)
                else:
                    input_queue.put(("right_click", (x, y)))
                    log.info(f"✖ Destroyed egg: {species_raw}")

                self.tracker.save()
                time.sleep(self.config.settings.get("scan_loop_delay", 0.5))

            except Exception:
                log.exception("Error in live scan loop")
                self.live_running = False
                break

    def quit_app(self):
        self.live_running = False
        self.destroy()
    def toggle_pause(self):
        """Pause/resume the live scan loop (F9)."""
        self.scanning_paused = not getattr(self, "scanning_paused", False)
        state = "Paused" if self.scanning_paused else "Resumed"
        log.info(f"⏸ {state}")


if __name__ == "__main__":
    app = SettingsEditor()
    app.mainloop()
