#!/usr/bin/env python3
import os, json, time
import cv2, numpy as np, pyautogui, keyboard

SETTINGS_FILE = "settings.json"

def wait_and_record(prompt):
    print(prompt)
    keyboard.wait("f9")
    x, y = pyautogui.position()
    print(f"  → recorded: ({x}, {y})\n")
    time.sleep(0.2)
    return x, y

def draw_roi(prompt, img):
    # create a resizable, always-on-top window
    cv2.namedWindow(prompt, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(prompt, cv2.WND_PROP_TOPMOST, 1)
    # maximize to screen size
    sw, sh = pyautogui.size()
    cv2.resizeWindow(prompt, sw, sh)

    roi = cv2.selectROI(prompt, img, showCrosshair=False, fromCenter=False)
    cv2.destroyWindow(prompt)
    x, y, w, h = map(int, roi)
    print(f"  → ROI = {{'x':{x}, 'y':{y}, 'w':{w}, 'h':{h}}}\n")
    return {"x": x, "y": y, "w": w, "h": h}

def main():
    print("=== Ark Single-Slot Scanner Calibration ===\n")

    # 1) Egg slot
    slot_x, slot_y = wait_and_record("1) Hover over an EGG SLOT and press F9")

    # open right-click menu to capture 'Destroy'
    pyautogui.moveTo(slot_x, slot_y)
    pyautogui.rightClick()
    time.sleep(0.5)

    # 2) 'Destroy'
    dest_x, dest_y = wait_and_record("2) Hover over 'Destroy' and press F9")
    destroy_offsets = [dest_x - slot_x, dest_y - slot_y]

    # 3) 'This'
    this_x, this_y = wait_and_record("3) Hover over 'This' submenu and press F9")
    destroy_this_offsets = [this_x - slot_x, this_y - slot_y]

    # 4) Open stats popup
    print("4) Opening stats popup…")
    pyautogui.click(slot_x, slot_y)
    time.sleep(0.5)

    # 5) Screenshot + popup ROI
    full = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    popup_roi = draw_roi("5) Draw ROI around the STATS POPUP and press ENTER", full)
    px, py_, pw, ph = popup_roi["x"], popup_roi["y"], popup_roi["w"], popup_roi["h"]
    popup_img = full[py_:py_+ph, px:px+pw]

    # 6) Species ROI
    species_roi = draw_roi(
        "6) Draw ROI around SPECIES NAME and press ENTER",
        popup_img
    )
    # convert back to screen coordinates
    species_roi["x"] += px
    species_roi["y"] += py_

    # 7) Stat ROIs (all drawn on popup_img)
    stat_rois = {}
    for stat in ("health","stamina","weight","melee","food","oxygen"):
        r = draw_roi(f"Draw ROI for STAT '{stat}' and press ENTER", popup_img)
        r["x"] += px
        r["y"] += py_
        stat_rois[stat] = r

    # 8) Hotkey, delays, debug flag
    hk = input("Enter scan hotkey (default F8): ").strip() or "F8"
    pd = input("Popup delay sec (default 0.25): ").strip()
    popup_delay = float(pd) if pd else 0.25
    ad = input("Action delay sec (default 0.05): ").strip()
    action_delay = float(ad) if ad else 0.05
    debug_mode = input("Enable debug mode? (y/N): ").strip().lower() == "y"

    # 10) Drop ALL EGGS button & confirmation
    drop_all_button  = wait_and_record("10) Hover over the 'Drop All Eggs' button and press F9")

    # 12–14) Food‐slot positions (we’ll assume 3 slots)
    food_slots = []
    for i in range(1, 4):
        pos = wait_and_record(f"{11+i}) Hover over FOOD SLOT {i} and press F9")
        food_slots.append(pos)

    # 9) Save settings
    cfg = {
        "slot_x":                slot_x,
        "slot_y":                slot_y,
        "destroy_offsets":       destroy_offsets,
        "destroy_this_offsets":  destroy_this_offsets,
        "popup_delay":           popup_delay,
        "action_delay":          action_delay,
        "hotkey_scan":           hk,
        "debug_mode":            debug_mode,
        "drop_all_button":       drop_all_button,
        "food_slots":            food_slots,
        "species_roi":           species_roi,
        "stat_rois":             stat_rois,
        "ocr": {
            "tesseract_cmd": "tesseract",
            "oem":           3,
            "psm":           7
        }
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    print(f"\n✅ Calibration complete — saved to {SETTINGS_FILE}")

if __name__ == "__main__":
    main()
