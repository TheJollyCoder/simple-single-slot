import tkinter as tk
from tkinter import ttk, scrolledtext
import time
from scanner import scan_slot
from utils.helpers import add_tooltip
from utils.calibration import run_calibration as calibration_wizard
from utils.dialogs import show_error

FONT = ("Segoe UI", 10)

# Prevent pytest from treating this UI module as a test
__test__ = False
from breeding_logic import should_keep_egg
from progress_tracker import (
    load_progress, save_progress,
    update_mutation_thresholds,
    update_stud, update_mutation_stud,
    normalize_species_name
)

def build_test_tab(app):
    ttk.Label(app.tab_test, text="Main Scripts", font=(FONT[0], FONT[1], "bold")).pack(pady=(10, 2))

    app.btn_start = ttk.Button(app.tab_test, text="Start Live Scanning (F8)", command=app.start_live_run)
    app.btn_start.pack(pady=5)
    add_tooltip(app.btn_start, "Start the automated scan loop using current settings")

    app.btn_pause = ttk.Button(
        app.tab_test,
        text="Pause Scanning",
        command=lambda: app.toggle_pause(True),
        state="disabled",
    )
    app.btn_pause.pack(pady=5)
    add_tooltip(app.btn_pause, "Pause the live scanning loop")

    app.btn_resume = ttk.Button(
        app.tab_test,
        text="Resume Scanning",
        command=lambda: app.toggle_pause(False),
        state="disabled",
    )
    app.btn_resume.pack(pady=5)
    add_tooltip(app.btn_resume, "Resume scanning after a pause")

    btn = ttk.Button(app.tab_test, text="Scan Egg", command=lambda: test_scan_egg(app))
    btn.pack(pady=5)
    add_tooltip(btn, "Perform one manual scan of the configured slot")

    # scrolling log viewer
    app.log_widget = scrolledtext.ScrolledText(app.tab_test, height=15, state="disabled")
    app.log_widget.pack(fill="both", expand=True, padx=5, pady=5)

    btn_clear = ttk.Button(app.tab_test, text="Clear Log", command=lambda: clear_log(app))
    btn_clear.pack(pady=(0, 10))
    add_tooltip(btn_clear, "Erase all entries from the log viewer")

    btn_cal = ttk.Button(app.tab_test, text="Run Calibration", command=run_calibration)
    btn_cal.pack(pady=(0, 10))
    add_tooltip(btn_cal, "Launch the calibration tool to record screen positions")

    ttk.Label(app.tab_test, text="Testing Utilities", font=(FONT[0], FONT[1], "bold")).pack(pady=(20, 2))
    btn = ttk.Button(app.tab_test, text="Force KEEP (Real Logic)", command=app.keep_egg)
    btn.pack(pady=5)
    add_tooltip(btn, "Force the keep logic on the current egg")
    btn = ttk.Button(app.tab_test, text="Force DESTROY (Real Logic)", command=app.destroy_egg)
    btn.pack(pady=5)
    add_tooltip(btn, "Force the destroy logic on the current egg")



def test_scan_egg(app):
    if getattr(app, "scanning_paused", False):
        print("🔁 Scanning is paused. Press F9 to resume.")
        return

    scan = scan_slot(app.settings)
    if scan == "no_egg":
        print("→ No egg detected.")
        return

    egg = scan["species"]
    stats = scan["stats"]
    sex = "female" if "female" in egg.lower() else "male"
    normalized = normalize_species_name(egg)

    config = app.rules.get(normalized, app.settings.get("default_species_template", {}))
    wipe = app.settings.get("current_wipe", "default")
    progress = load_progress(wipe)

    updated_thresholds = update_mutation_thresholds(egg, stats, config, progress, sex, wipe)
    updated_stud = False
    updated_mutation_stud = False
    if sex == "male":
        updated_stud = update_stud(egg, stats, config, progress, wipe)
        updated_mutation_stud = update_mutation_stud(egg, stats, config, progress)

    scan.update({
        "egg": egg,
        "sex": sex,
        "stats": stats,
        "updated_thresholds": updated_thresholds,
        "updated_stud": updated_stud,
        "updated_mutation_stud": updated_mutation_stud,
    })

    decision, reasons = should_keep_egg(scan, config, progress)
    save_progress(progress, wipe)

    print(f"→ Scanned Egg: {egg} | DECISION: {decision.upper()}")
    for k, v in reasons.items():
        if k != "_debug" and v:
            print(f"  ✔ {k}")
    debug_cfg = app.settings.get("debug_mode", False)
    debug_enabled = (
        debug_cfg.get("breeding_logic", False)
        if isinstance(debug_cfg, dict)
        else bool(debug_cfg)
    )
    if debug_enabled and "_debug" in reasons:
        for k, v in reasons["_debug"].items():
            print(f"    debug[{k}]: {v}")

    if decision == "keep":
        import pyautogui
        pyautogui.doubleClick(app.settings["slot_x"], app.settings["slot_y"])
        print("✔ Egg auto-kept via double-click")


def clear_log(app):
    """Remove all text from the on-screen log widget."""
    if hasattr(app, "log_widget"):
        app.log_widget.configure(state="normal")
        app.log_widget.delete("1.0", "end")
        app.log_widget.configure(state="disabled")

def run_calibration():
    """Launch the calibration wizard inside the application."""
    try:
        calibration_wizard()
    except Exception as e:
        show_error("Error", str(e))

