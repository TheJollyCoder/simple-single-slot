import tkinter as tk
from tkinter import ttk, scrolledtext
import time
from scanner import scan_slot
from utils.helpers import add_tooltip

FONT = ("Segoe UI", 10)

# Prevent pytest from treating this UI module as a test
__test__ = False
from breeding_logic import should_keep_egg
from progress_tracker import (
    load_progress, save_progress,
    update_top_stats, update_mutation_thresholds,
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

    ttk.Label(app.tab_test, text="Testing Utilities", font=(FONT[0], FONT[1], "bold")).pack(pady=(20, 2))
    btn = ttk.Button(app.tab_test, text="Force KEEP (Real Logic)", command=app.keep_egg)
    btn.pack(pady=5)
    add_tooltip(btn, "Force the keep logic on the current egg")
    btn = ttk.Button(app.tab_test, text="Force DESTROY (Real Logic)", command=app.destroy_egg)
    btn.pack(pady=5)
    add_tooltip(btn, "Force the destroy logic on the current egg")
    btn = ttk.Button(app.tab_test, text="Multi-Egg Scan Test", command=lambda: multi_egg_test(app))
    btn.pack(pady=10)
    add_tooltip(btn, "Run repeated scans for debugging")



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
    progress = load_progress(app.settings.get("current_wipe", "default"))
    new_species = normalized not in progress
    if new_species and normalized not in app.rules:
        from copy import deepcopy
        app.rules[normalized] = deepcopy(app.settings.get("default_species_template", {}))
        with open("rules.json", "w", encoding="utf-8") as f:
            json.dump(app.rules, f, indent=2)
        from utils.helpers import refresh_species_dropdown
        refresh_species_dropdown(app)

    update_top_stats(egg, stats, progress)
    update_mutation_thresholds(egg, stats, config, progress, sex)
    if sex == "male":
        update_stud(egg, stats, config, progress)
        update_mutation_stud(egg, stats, config, progress)

    scan.update({
        "egg": egg,
        "sex": sex,
        "stats": stats,
        "updated_stats": update_top_stats(egg, stats, progress),
        "updated_thresholds": update_mutation_thresholds(egg, stats, config, progress, sex),
        "updated_stud": update_stud(egg, stats, config, progress) if sex == "male" else False,
        "updated_mutation_stud": update_mutation_stud(egg, stats, config, progress) if sex == "male" else False
    })

    decision, reasons = should_keep_egg(scan, config, progress)
    save_progress(progress, app.settings.get("current_wipe", "default"))

    print(f"→ Scanned Egg: {egg} | DECISION: {decision.upper()}")
    for k, v in reasons.items():
        if k != "_debug" and v:
            print(f"  ✔ {k}")
    if "_debug" in reasons:
        for k, v in reasons["_debug"].items():
            print(f"    debug[{k}]: {v}")

    if decision == "keep":
        import pyautogui
        pyautogui.doubleClick(app.settings["slot_x"], app.settings["slot_y"])
        print("✔ Egg auto-kept via double-click")

def multi_egg_test(app):
    try:
        count = int(input("How many eggs to scan for test? "))
    except:
        print("Invalid number.")
        return
    print(f"Scanning {count} eggs...")
    progress = load_progress(app.settings.get("current_wipe", "default"))

    for i in range(1, count + 1):
        if getattr(app, "scanning_paused", False):
            print(f"🔁 Skipping scan {i}, scanning is paused.")
            continue

        scan = scan_slot(app.settings)
        if scan == "no_egg":
            print(f"Egg {i}: no egg found.")
            continue

        egg = scan["species"]
        stats = scan["stats"]
        sex = "female" if "female" in egg.lower() else "male"
        normalized = normalize_species_name(egg)

        config = app.rules.get(normalized, app.settings.get("default_species_template", {}))
        new_species = normalized not in progress
        if new_species and normalized not in app.rules:
            from copy import deepcopy
            app.rules[normalized] = deepcopy(app.settings.get("default_species_template", {}))
            with open("rules.json", "w", encoding="utf-8") as f:
                json.dump(app.rules, f, indent=2)
            from utils.helpers import refresh_species_dropdown
            refresh_species_dropdown(app)
        update_top_stats(egg, stats, progress)
        update_mutation_thresholds(egg, stats, config, progress, sex)
        if sex == "male":
            update_stud(egg, stats, config, progress)
            update_mutation_stud(egg, stats, config, progress)

        scan.update({
            "egg": egg,
            "sex": sex,
            "stats": stats,
            "updated_stats": update_top_stats(egg, stats, progress),
            "updated_thresholds": update_mutation_thresholds(egg, stats, config, progress, sex),
            "updated_stud": update_stud(egg, stats, config, progress) if sex == "male" else False,
            "updated_mutation_stud": update_mutation_stud(egg, stats, config, progress) if sex == "male" else False
        })

        decision, reasons = should_keep_egg(scan, config, progress)
        save_progress(progress, app.settings.get("current_wipe", "default"))

        print(f"Egg {i}: {egg} | DECISION: {decision.upper()}")
        for k, v in reasons.items():
            if k != "_debug" and v:
                print(f"  ✔ {k}")
        if "_debug" in reasons:
            for k, v in reasons["_debug"].items():
                print(f"    debug[{k}]: {v}")
        if decision == "keep":
            import pyautogui
            pyautogui.doubleClick(app.settings["slot_x"], app.settings["slot_y"])
            print("→ Egg auto-kept via double-click")
