import tkinter as tk
import pyautogui
import time
from logger import get_logger

log = get_logger("test_tab")
from scanner import scan_slot
from breeding_logic import should_keep_egg
from progress_tracker import (
    load_progress, save_progress,
    update_top_stats, update_mutation_thresholds, update_stud,
    normalize_species_name
)

def build_test_tab(app):
    tk.Label(app.tab_test, text="Main Scripts", font=("Segoe UI", 10, "bold")).pack(pady=(10, 2))
    tk.Button(app.tab_test, text="Start Live Scanning (F8)", command=app.start_live_run).pack(pady=5)
    tk.Button(app.tab_test, text="Scan Egg", command=lambda: test_scan_egg(app)).pack(pady=5)

    tk.Label(app.tab_test, text="Testing Utilities", font=("Segoe UI", 10, "bold")).pack(pady=(20, 2))
    tk.Button(app.tab_test, text="Force KEEP (Real Logic)", command=app.keep_egg).pack(pady=5)
    tk.Button(app.tab_test, text="Force DESTROY (Real Logic)", command=app.destroy_egg).pack(pady=5)
    tk.Button(app.tab_test, text="Multi-Egg Scan Test", command=lambda: multi_egg_test(app)).pack(pady=10)



def test_scan_egg(app):
    if getattr(app, "scanning_paused", False):
        log.info("🔁 Scanning is paused. Press F9 to resume.")
        return

    scan = scan_slot(app.settings)
    if scan == "no_egg":
        log.info("→ No egg detected.")
        return

    egg = scan["species"]
    stats = scan["stats"]
    sex = "female" if "female" in egg.lower() else "male"
    normalized = normalize_species_name(egg)

    config = app.rules.get(normalized, app.settings.get("default_species_template", {}))
    progress = load_progress()

    update_top_stats(egg, stats, progress)
    update_mutation_thresholds(egg, stats, config, progress, sex)
    if sex == "male":
        update_stud(egg, stats, config, progress)

    scan.update({
        "egg": egg,
        "sex": sex,
        "stats": stats,
        "updated_stats": update_top_stats(egg, stats, progress),
        "updated_thresholds": update_mutation_thresholds(egg, stats, config, progress, sex),
        "updated_stud": update_stud(egg, stats, config, progress) if sex == "male" else False
    })

    decision, reasons = should_keep_egg(scan, config, progress)
    save_progress(progress)

    log.info(f"→ Scanned Egg: {egg} | DECISION: {decision.upper()}")
    for k, v in reasons.items():
        if k != "_debug" and v:
            log.info(f"  ✔ {k}")
    if "_debug" in reasons:
        for k, v in reasons["_debug"].items():
            log.info(f"    debug[{k}]: {v}")

    if decision == "keep":
        pyautogui.doubleClick(app.settings["slot_x"], app.settings["slot_y"])
        log.info("✔ Egg auto-kept via double-click")

def multi_egg_test(app):
    try:
        count = int(input("How many eggs to scan for test? "))
    except:
        log.info("Invalid number.")
        return
    log.info(f"Scanning {count} eggs...")
    progress = load_progress()

    for i in range(1, count + 1):
        if getattr(app, "scanning_paused", False):
            log.info(f"🔁 Skipping scan {i}, scanning is paused.")
            continue

        scan = scan_slot(app.settings)
        if scan == "no_egg":
            log.info(f"Egg {i}: no egg found.")
            continue

        egg = scan["species"]
        stats = scan["stats"]
        sex = "female" if "female" in egg.lower() else "male"
        normalized = normalize_species_name(egg)

        config = app.rules.get(normalized, app.settings.get("default_species_template", {}))
        update_top_stats(egg, stats, progress)
        update_mutation_thresholds(egg, stats, config, progress, sex)
        if sex == "male":
            update_stud(egg, stats, config, progress)

        scan.update({
            "egg": egg,
            "sex": sex,
            "stats": stats,
            "updated_stats": update_top_stats(egg, stats, progress),
            "updated_thresholds": update_mutation_thresholds(egg, stats, config, progress, sex),
            "updated_stud": update_stud(egg, stats, config, progress) if sex == "male" else False
        })

        decision, reasons = should_keep_egg(scan, config, progress)
        save_progress(progress)

        log.info(f"Egg {i}: {egg} | DECISION: {decision.upper()}")
        for k, v in reasons.items():
            if k != "_debug" and v:
                log.info(f"  ✔ {k}")
        if "_debug" in reasons:
            for k, v in reasons["_debug"].items():
                log.info(f"    debug[{k}]: {v}")
        if decision == "keep":
            pyautogui.doubleClick(app.settings["slot_x"], app.settings["slot_y"])
            log.info("→ Egg auto-kept via double-click")
