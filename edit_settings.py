import os
import json
import time
import threading
import subprocess
import pyautogui
import keyboard
import tkinter as tk
from tkinter import ttk, messagebox

from scanner import scan_slot
from breeding_logic import should_keep_egg
from progress_tracker import (
    load_progress, save_progress,
    update_top_stats, update_mutation_thresholds, update_stud,
    normalize_species_name
)

from tabs.global_tab import build_global_tab
from tabs.species_tab import build_species_tab
from tabs.tools_tab import build_tools_tab
from tabs.test_tab import build_test_tab

SETTINGS_FILE = "settings.json"
RULES_FILE    = "rules.json"
PROGRESS_FILE = "breeding_progress.json"

DEFAULT_MODES = ["mutations", "all_females", "stat_merge", "top_stat_females", "war"]
ALL_STATS     = ["health", "stamina", "weight", "melee", "food", "oxygen"]

# ─── Load or initialize data ─────────────────────────────────────
settings = json.load(open(SETTINGS_FILE, encoding="utf-8")) if os.path.exists(SETTINGS_FILE) else {}
rules    = json.load(open(RULES_FILE,    encoding="utf-8")) if os.path.exists(RULES_FILE)    else {}
progress = json.load(open(PROGRESS_FILE, encoding="utf-8")) if os.path.exists(PROGRESS_FILE) else {}

default_species_template = settings.get("default_species_template", {
    "modes": ["mutations", "all_females"],
    "mutation_stats": ["health", "melee"],
    "stat_merge_stats": ["health", "melee", "stamina"],
    "top_stat_females_stats": ["health", "melee", "stamina"],
    "war_stats": ["health", "melee", "stamina"]
})

# ensure every species in progress has a rules entry
for species in progress:
    if species not in rules:
        rules[species] = default_species_template.copy()

# ─── Main GUI ─────────────────────────────────────────────────────
class SettingsEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ARK Breeding Config Editor")
        self.geometry("750x600")

        # data handles
        self.settings = settings
        self.rules    = rules
        self.progress = progress

        # summary buffers for ESC dump
        self._summary = {"studs": [], "mutations": []}

        # UI state variables
        self.selected_species      = tk.StringVar()
        self.default_modes         = tk.StringVar(value=DEFAULT_MODES)
        self.mode_vars             = {m: tk.BooleanVar(value=True) for m in DEFAULT_MODES}
        self.stat_vars             = {s: tk.BooleanVar(value=True) for s in ALL_STATS}
        self.mutation_stat_vars    = {s: tk.BooleanVar(value=True) for s in ALL_STATS}

        # build all tabs
        self.create_tabs()

        # hotkeys
        keyboard.add_hotkey(self.settings.get("hotkey_scan", "F8"), self.start_live_run)
        keyboard.add_hotkey("esc", self.quit)

    def save_all(self):
        """Save settings.json and rules.json from GUI state."""
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2)
        with open(RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.rules, f, indent=2)
        messagebox.showinfo("Saved", "Settings and rules have been saved.")

    def create_tabs(self):
        """Construct the Notebook and attach each tab’s builder."""
        tabs = ttk.Notebook(self)
        tabs.pack(expand=True, fill="both")

        self.tab_global  = ttk.Frame(tabs); tabs.add(self.tab_global,  text="Global Settings")
        self.tab_species = ttk.Frame(tabs); tabs.add(self.tab_species, text="Species Config")
        self.tab_tools   = ttk.Frame(tabs); tabs.add(self.tab_tools,   text="Defaults & Tools")
        self.tab_test    = ttk.Frame(tabs); tabs.add(self.tab_test,    text="Script Control")

        build_global_tab(self)
        build_species_tab(self)
        build_tools_tab(self)
        build_test_tab(self)

    def start_live_run(self):
        """Begin background live‐scan loop (F8)."""
        if getattr(self, "live_running", False):
            print("⚠️ Already running.")
            return

        # reset summary each run
        self._summary = {"studs": [], "mutations": []}
        self.live_running = True
        self.scanning_paused = False

        def run_loop():
            print("▶️ Live scanning started (F8 to run, F9 to pause/resume, ESC to exit)")
            while self.live_running:
                if self.scanning_paused:
                    time.sleep(0.1)
                    continue

                scan = scan_slot(self.settings)
                if scan == "no_egg":
                    print("→ No egg detected.")
                    time.sleep(self.settings.get("scan_loop_delay", 0.5))
                    continue

                egg        = scan["species"]
                stats      = scan["stats"]
                sex        = "female" if "female" in egg.lower() else "male"
                normalized = normalize_species_name(egg)

                config   = self.rules.get(normalized, self.settings.get("default_species_template", {}))
                progress = load_progress()

                # Step 1: update top‐stats
                updated_stats = update_top_stats(egg, stats, progress)

                # Step 2: decide keep/destroy
                decision, reasons = should_keep_egg(
                    {"egg": egg, "sex": sex, "stats": stats},
                    config,
                    progress
                )

                # Step 3: update thresholds only if mutations rule passed
                if reasons.get("mutations"):
                    updated_thresholds = update_mutation_thresholds(
                        egg, stats, config, progress, sex
                    )
                else:
                    updated_thresholds = False

                # and only then update stud logic
                updated_stud = (
                    update_stud(egg, stats, config, progress)
                    if sex == "male"
                    else False
                )

                # record for summary
                if updated_thresholds:
                    curr = progress[normalized]["mutation_thresholds"].copy()
                    self._summary["mutations"].append((normalized, curr))
                if updated_stud:
                    self._summary["studs"].append((normalized, stats))

                # Step 4: save progress & UI feedback
                scan.update({
                    "egg": egg,
                    "sex": sex,
                    "stats": stats,
                    "updated_stats": updated_stats,
                    "updated_thresholds": updated_thresholds,
                    "updated_stud": updated_stud
                })
                save_progress(progress)
                # print UI feedback
                print(f"→ {egg}: {decision.upper()}")
                for k, v in reasons.items():
                    if k != "_debug" and v:
                        print(f"  ✔ {k}")
                if "_debug" in reasons:
                    for k, v in reasons["_debug"].items():
                        print(f"    debug[{k}]: {v}")

                if decision == "keep":
                    pyautogui.doubleClick(self.settings["slot_x"], self.settings["slot_y"])
                    print("✔ Egg auto-kept via double-click")
                else:
                    x, y   = self.settings["slot_x"], self.settings["slot_y"]
                    dx, dy       = self.settings["destroy_offsets"]
                    dx2, dy2     = self.settings["destroy_this_offsets"]
                    pyautogui.moveTo(x, y); pyautogui.rightClick()
                    time.sleep(0.3)
                    pyautogui.moveTo(x + dx, y + dy)
                    time.sleep(0.3)
                    pyautogui.moveTo(x + dx2, y + dy2); pyautogui.click()
                    print("✖ Egg destroyed via right-click chain")

                time.sleep(self.settings.get("scan_loop_delay", 0.5))

            self.live_running = False
            print("⏹ Scanning stopped.")

        # pause/resume toggle
        def toggle_pause():
            self.scanning_paused = not self.scanning_paused
            print("⏸ Paused" if self.scanning_paused else "▶️ Resumed")

        threading.Thread(target=run_loop, daemon=True).start()
        keyboard.add_hotkey("f9", toggle_pause)

    def keep_egg(self):
        """Button: force KEEP via real logic."""
        pyautogui.doubleClick(self.settings["slot_x"], self.settings["slot_y"])
        print("✔ KEEP action invoked")

    def destroy_egg(self):
        """Button: force DESTROY via real logic."""
        x, y       = self.settings["slot_x"], self.settings["slot_y"]
        dx, dy     = self.settings["destroy_offsets"]
        dx2, dy2   = self.settings["destroy_this_offsets"]
        pyautogui.moveTo(x, y); pyautogui.rightClick()
        time.sleep(0.3)
        pyautogui.moveTo(x + dx, y + dy)
        time.sleep(0.3)
        pyautogui.moveTo(x + dx2, y + dy2); pyautogui.click()
        print("✖ DESTROY action invoked")

    def quit(self):
        """On ESC: write summary.log then close."""
        print("🛑 ESC pressed — quitting application.")
        with open("summary.log", "w", encoding="utf-8") as f:
            f.write("=== STUDS UPDATED (tracked only) ===\n")
            for species, stats in self._summary["studs"]:
                tracked = self.rules.get(species, {}).get("stat_merge_stats", [])
                parts = []
                for st in tracked:
                    v = stats.get(st, {"base": 0, "mutation": 0})
                    b, m = v["base"], v["mutation"]
                    parts.append(f"{b}({m}){st[0].upper()}" if m else f"{b}{st[0].upper()}")
                f.write(" ".join(parts) + f" {species}\n")

            f.write("\n=== MUTATION THRESHOLDS ===\n")
            for species, thresh in self._summary["mutations"]:
                parts = [f"{val}{stat[0].upper()}" for stat, val in thresh.items()]
                f.write(" ".join(parts) + f" {species}\n")

        print("✅ Summary written to summary.log")
        self.destroy()

if __name__ == "__main__":
    app = SettingsEditor()
    app.mainloop()
