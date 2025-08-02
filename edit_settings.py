import os
import json
import time
import threading
import subprocess
import pyautogui
import keyboard
import tkinter as tk
from tkinter import ttk
from copy import deepcopy
from utils.dialogs import show_error, show_warning, show_info
import webbrowser

from scanner import scan_slot
from breeding_logic import should_keep_egg
from progress_tracker import (
    load_progress, save_progress,
    update_mutation_thresholds,
    update_stud, update_mutation_stud,
    increment_female_count, adjust_rules_for_females,
    normalize_species_name
)

from tabs.global_tab import build_global_tab
from tabs.species_tab import build_species_tab
from tabs.tools_tab import build_tools_tab
from tabs.script_control_tab import build_test_tab, prompt_new_species
from tabs.progress_tab import build_stats_tab
from utils.config_validator import validate_configs
from utils.helpers import refresh_species_dropdown

SETTINGS_FILE = "settings.json"
RULES_FILE = "rules.json"

# maximum number of lines to retain in the on-screen log viewer
MAX_LOG_LINES = 500

DEFAULT_MODES = [
    "mutations",
    "all_females",
    "stat_merge",
    "top_stat_females",
    "war",
    "automated",
]
ALL_STATS = ["health", "stamina", "weight", "melee", "food", "oxygen"]

# ─── Load or initialize data ─────────────────────────────────────
settings = (
    json.load(open(SETTINGS_FILE, encoding="utf-8"))
    if os.path.exists(SETTINGS_FILE)
    else {}
)
rules = (
    json.load(open(RULES_FILE, encoding="utf-8"))
    if os.path.exists(RULES_FILE)
    else {}
)
progress = load_progress(settings.get("current_wipe", "default"))

default_species_template = settings.get("default_species_template", {
    "modes": ["mutations", "all_females", "stat_merge", "top_stat_females", "war", "automated"],
    "mutation_stats": ["health", "melee"],
    "stat_merge_stats": ["health", "melee", "stamina"],
    "top_stat_females_stats": ["health", "melee", "stamina"],
    "war_stats": ["health", "melee", "stamina"]
})

# ensure every species in progress has a rules entry
for species in progress:
    if species not in rules:
        rules[species] = deepcopy(default_species_template)
        modes = set(rules[species].get("modes", []))
        modes.add("automated")
        rules[species]["modes"] = list(modes)

# ─── Main GUI ─────────────────────────────────────────────────────
class SettingsEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ARK Breeding Config Editor")

        # global ttk style
        self.style = ttk.Style(self)

        # menus
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Save", command=self.save_all)
        file_menu.add_command(label="Quit", command=self.quit)
        menu.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(
            label="Documentation",
            command=lambda: webbrowser.open("https://example.com"),
        )
        menu.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menu)

        self.bind_all("<Control-s>", lambda e: self.save_all())
        self.bind_all("<Control-q>", lambda e: self.quit())

        # data handles
        self.settings = settings
        self.rules = rules
        self.progress = progress

        if self.settings.get("window_geometry"):
            self.geometry(self.settings.get("window_geometry"))
        else:
            self.geometry("750x600")

        # summary buffers for ESC dump
        self._summary = {"studs": [], "mutations": []}

        # UI state variables
        self.selected_species = tk.StringVar()
        self.default_modes = tk.StringVar(value=DEFAULT_MODES)
        self.mode_vars = {m: tk.BooleanVar(value=True) for m in DEFAULT_MODES}
        self.stat_vars = {s: tk.BooleanVar(value=True) for s in ALL_STATS}
        self.mutation_stat_vars = {
            s: tk.BooleanVar(value=True) for s in ALL_STATS
        }

        # build all tabs
        self.create_tabs()

        # status indicator at bottom of window
        self.status_frame = ttk.Frame(self)
        self.status_icon = tk.Label(self.status_frame, text="\u25CF", fg="gray")
        self.status_icon.pack(side="left", padx=(5, 2))
        self.status_lbl = ttk.Label(self.status_frame, text="Idle")
        self.status_lbl.pack(side="left")
        self.status_frame.pack(side="bottom", fill="x")

        # hotkeys
        self.update_hotkeys(initial=True)

        warnings = validate_configs(self.settings, self.rules, self.progress)
        if warnings:
            show_warning("Config Warnings", "\n".join(warnings))

    def save_geometry(self):
        """Store current window geometry into settings."""
        self.settings["window_geometry"] = self.geometry()

    def save_all(self):
        """Save settings.json and rules.json from GUI state."""
        self.save_geometry()
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2)
        with open(RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.rules, f, indent=2)
        show_info("Saved", "Settings and rules have been saved.")

    def create_tabs(self):
        """Construct the Notebook and attach each tab’s builder."""
        tabs = ttk.Notebook(self)
        tabs.pack(expand=True, fill="both")

        self.tab_test = ttk.Frame(tabs)
        tabs.add(self.tab_test, text="Script Control")
        self.tab_global = ttk.Frame(tabs)
        tabs.add(self.tab_global, text="Global Settings")
        self.tab_species = ttk.Frame(tabs)
        tabs.add(self.tab_species, text="Species Config")
        self.tab_tools = ttk.Frame(tabs)
        tabs.add(self.tab_tools, text="Defaults")
        self.tab_stats = ttk.Frame(tabs)
        tabs.add(self.tab_stats, text="Studs")
        self.tab_stat_list = ttk.Frame(tabs)
        tabs.add(self.tab_stat_list, text="Stat List")
        self.tab_help = ttk.Frame(tabs)
        tabs.add(self.tab_help, text="Help")

        build_test_tab(self)
        build_global_tab(self)
        build_species_tab(self)
        build_tools_tab(self)
        build_stats_tab(self)
        from tabs.stat_list_tab import build_stat_list_tab
        build_stat_list_tab(self)
        from tabs.help_tab import build_help_tab
        build_help_tab(self)

    def log_message(self, msg: str):
        """Write a line to both stdout and the GUI log viewer."""
        try:
            if hasattr(self, "log_widget"):
                self.log_widget.configure(state="normal")
                try:
                    lines = int(self.log_widget.index("end-1c").split(".")[0])
                except Exception:
                    lines = 0
                while lines >= MAX_LOG_LINES:
                    try:
                        self.log_widget.delete("1.0", "2.0")
                        lines = int(self.log_widget.index("end-1c").split(".")[0])
                    except Exception:
                        break
                self.log_widget.insert("end", msg + "\n")
                self.log_widget.see("end")
                self.log_widget.configure(state="disabled")
        except Exception:
            pass
        print(msg)

    def update_status(self, msg: str):
        """Update bottom status label and colored indicator."""
        if hasattr(self, "status_lbl"):
            self.status_lbl["text"] = msg
        if hasattr(self, "status_icon"):
            colors = {"Running": "green", "Paused": "orange", "Stopped": "red", "Saved": "blue"}
            self.status_icon.config(fg=colors.get(msg, "gray"))

    def flash_status(self, msg: str, duration: int = 2) -> None:
        """Temporarily show a status message then revert to Idle."""
        self.update_status(msg)
        try:
            self.after(int(duration * 1000), lambda: self.update_status("Idle"))
        except Exception:
            pass

    def update_hotkeys(self, initial: bool = False):
        """Refresh global hotkeys based on current settings."""
        for h in getattr(self, "_hotkey_handles", []):
            try:
                keyboard.remove_hotkey(h)
            except Exception:
                pass
        self._hotkey_handles = []
        scan_key = self.settings.get("hotkey_scan", "F8")
        self._hotkey_handles.append(keyboard.add_hotkey(scan_key, self.start_live_run))
        self._hotkey_handles.append(keyboard.add_hotkey("esc", self.quit))

    def toggle_pause(self, value=None):
        """Pause or resume scanning."""
        if value is None:
            self.scanning_paused = not getattr(self, "scanning_paused", False)
        else:
            self.scanning_paused = bool(value)
        self.log_message("⏸ Paused" if self.scanning_paused else "▶️ Resumed")
        self.update_status("Paused" if self.scanning_paused else "Running")
        if hasattr(self, "btn_pause") and hasattr(self, "btn_resume"):
            if self.scanning_paused:
                self.btn_pause.config(state="disabled")
                self.btn_resume.config(state="normal")
            else:
                self.btn_pause.config(state="normal")
                self.btn_resume.config(state="disabled")

    def start_live_run(self):
        """Begin background live‐scan loop (F8)."""
        if getattr(self, "live_running", False):
            self.log_message("⚠️ Already running.")
            return

        # reset summary each run
        self._summary = {"studs": [], "mutations": []}
        self.live_running = True
        self.scanning_paused = False
        self.update_status("Running")

        def run_loop():
            self.log_message("▶️ Live scanning started (F8 to run, F9 to pause/resume, ESC to exit)")
            while self.live_running:
                if self.scanning_paused:
                    time.sleep(0.1)
                    continue

                scan = scan_slot(self.settings)
                if scan == "no_egg":
                    self.log_message("→ No egg detected.")
                    time.sleep(self.settings.get("scan_loop_delay", 0.5))
                    continue

                egg = scan["species"]
                stats = scan["stats"]
                sex = "female" if "female" in egg.lower() else "male"
                normalized = normalize_species_name(egg)

                config = self.rules.get(normalized)
                wipe = self.settings.get("current_wipe", "default")
                progress = load_progress(wipe)
                new_species = False
                if config is None:
                    new_species = True
                    if self.settings.get("monitored_scan", True):
                        self.log_message(f"⏸ New species detected: {normalized}")
                        self.scanning_paused = True
                        self.update_status("Paused")
                        cfg = prompt_new_species(self, normalized)
                        self.scanning_paused = False
                        self.update_status("Running")
                        if cfg is None:
                            cfg = deepcopy(self.settings.get("default_species_template", {}))
                    else:
                        cfg = deepcopy(self.settings.get("default_species_template", {}))
                    modes = set(cfg.get("modes", []))
                    modes.add("automated")
                    cfg["modes"] = list(modes)
                    self.rules[normalized] = cfg
                    config = cfg
                    with open(RULES_FILE, "w", encoding="utf-8") as f:
                        json.dump(self.rules, f, indent=2)
                    self.log_message(f"✔ Added {normalized} to rules")

                # Step 1: decide keep/destroy
                decision, reasons = should_keep_egg(
                    {"egg": egg, "sex": sex, "stats": stats},
                    config,
                    progress
                )

                # Track kept females and adjust rules automatically
                if decision == "keep" and sex == "female":
                    count = increment_female_count(egg, progress, sex)
                    if adjust_rules_for_females(normalized, progress, self.rules, self.settings.get("default_species_template")):
                        with open(RULES_FILE, "w", encoding="utf-8") as f:
                            json.dump(self.rules, f, indent=2)
                        self.log_message(f"⚙ Rules updated for {normalized} (females={count})")

                # Step 2: update thresholds only if mutations rule passed
                if reasons.get("mutations"):
                    updated_thresholds = update_mutation_thresholds(
                        egg, stats, config, progress, sex, wipe
                    )
                else:
                    updated_thresholds = False

                # and only then update stud logic
                updated_stud = (
                    update_stud(egg, stats, config, progress, wipe)
                    if sex == "male"
                    else False
                )
                updated_mstud = (
                    update_mutation_stud(egg, stats, config, progress)
                    if sex == "male"
                    else False
                )

                # record for summary
                if updated_thresholds:
                    curr = progress[normalized]["mutation_thresholds"].copy()
                    self._summary["mutations"].append((normalized, curr))
                if updated_stud:
                    self._summary["studs"].append((normalized, stats))

                # Step 3: save progress & UI feedback
                scan.update({
                    "egg": egg,
                    "sex": sex,
                    "stats": stats,
                    "updated_thresholds": updated_thresholds,
                    "updated_stud": updated_stud,
                    "updated_mutation_stud": updated_mstud
                })
                save_progress(progress, wipe)
                if new_species:
                    refresh_species_dropdown(self)
                # print UI feedback
                self.log_message(f"→ {egg}: {decision.upper()}")
                for k, v in reasons.items():
                    if k != "_debug" and v:
                        self.log_message(f"  ✔ {k}")
                debug_cfg = self.settings.get("debug_mode", False)
                debug_enabled = (
                    debug_cfg.get("breeding_logic", False)
                    if isinstance(debug_cfg, dict)
                    else bool(debug_cfg)
                )
                if debug_enabled and "_debug" in reasons:
                    for k, v in reasons["_debug"].items():
                        self.log_message(f"    debug[{k}]: {v}")

                if decision == "keep":
                    pyautogui.doubleClick(self.settings["slot_x"], self.settings["slot_y"])
                    self.log_message("✔ Egg auto-kept via double-click")
                else:
                    x, y = self.settings["slot_x"], self.settings["slot_y"]
                    dx, dy = self.settings["destroy_offsets"]
                    dx2, dy2 = self.settings["destroy_this_offsets"]
                    pyautogui.moveTo(x, y); pyautogui.rightClick()
                    time.sleep(0.3)
                    pyautogui.moveTo(x + dx, y + dy)
                    time.sleep(0.3)
                    pyautogui.moveTo(x + dx2, y + dy2); pyautogui.click()
                    self.log_message("✖ Egg destroyed via right-click chain")

                time.sleep(self.settings.get("scan_loop_delay", 0.5))

            self.live_running = False
            self.log_message("⏹ Scanning stopped.")
            self.update_status("Stopped")
            if hasattr(self, "btn_start"):
                self.btn_start.config(state="normal")
            if hasattr(self, "btn_pause") and hasattr(self, "btn_resume"):
                self.btn_pause.config(state="disabled")
                self.btn_resume.config(state="disabled")
        # pause/resume toggle handled globally
        threading.Thread(target=run_loop, daemon=True).start()
        keyboard.add_hotkey("f9", self.toggle_pause)
        if hasattr(self, "btn_start"):
            self.btn_start.config(state="disabled")
        if hasattr(self, "btn_pause") and hasattr(self, "btn_resume"):
            self.btn_pause.config(state="normal")
            self.btn_resume.config(state="disabled")

    def keep_egg(self):
        """Button: force KEEP via real logic."""
        pyautogui.doubleClick(self.settings["slot_x"], self.settings["slot_y"])
        self.log_message("✔ KEEP action invoked")

    def destroy_egg(self):
        """Button: force DESTROY via real logic."""
        x, y = self.settings["slot_x"], self.settings["slot_y"]
        dx, dy = self.settings["destroy_offsets"]
        dx2, dy2 = self.settings["destroy_this_offsets"]
        pyautogui.moveTo(x, y); pyautogui.rightClick()
        time.sleep(0.3)
        pyautogui.moveTo(x + dx, y + dy)
        time.sleep(0.3)
        pyautogui.moveTo(x + dx2, y + dy2); pyautogui.click()
        self.log_message("✖ DESTROY action invoked")

    def quit(self):
        """On ESC: write summary.log then close."""
        self.log_message("🛑 ESC pressed — quitting application.")
        self.update_status("Stopped")
        self.save_geometry()
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

        self.log_message("✅ Summary written to summary.log")
        self.destroy()

if __name__ == "__main__":
    app = SettingsEditor()
    app.mainloop()
