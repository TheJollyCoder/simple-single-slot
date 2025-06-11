import json
import time
import tkinter as tk
from tkinter import messagebox, simpledialog

import cv2
import numpy as np
import pyautogui
import keyboard

SETTINGS_FILE = "settings.json"


def _popup(prompt: str, root: tk.Tk | None = None) -> tk.Toplevel:
    """Create a small top-level window with the given prompt."""
    win = tk.Toplevel(root)
    win.title("Calibration")
    label = tk.Label(win, text=prompt, padx=20, pady=20)
    label.pack()
    win.attributes("-topmost", True)
    win.update()
    return win


def wait_and_record_gui(prompt: str, root: tk.Tk | None = None):
    """Show ``prompt`` and return mouse position when F9 is pressed."""
    win = _popup(f"{prompt}\nPress F9 to record.", root)
    keyboard.wait("f9")
    x, y = pyautogui.position()
    win.destroy()
    time.sleep(0.2)
    return x, y


def draw_roi(prompt: str, img):
    """Display ``img`` and let the user draw a rectangle."""
    cv2.namedWindow(prompt, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(prompt, cv2.WND_PROP_TOPMOST, 1)
    sw, sh = pyautogui.size()
    cv2.resizeWindow(prompt, sw, sh)
    roi = cv2.selectROI(prompt, img, showCrosshair=False, fromCenter=False)
    cv2.destroyWindow(prompt)
    x, y, w, h = map(int, roi)
    return {"x": x, "y": y, "w": w, "h": h}


def run_calibration(root: tk.Tk | None = None) -> dict:
    """Interactive calibration with GUI prompts."""
    messagebox.showinfo(
        "Calibration",
        "Follow the prompts. Move your mouse to the requested location and press F9",
        parent=root,
    )

    slot_x, slot_y = wait_and_record_gui("1) Hover over an EGG SLOT", root)

    pyautogui.moveTo(slot_x, slot_y)
    pyautogui.rightClick()
    time.sleep(0.5)

    dest_x, dest_y = wait_and_record_gui("2) Hover over 'Destroy'", root)
    destroy_offsets = [dest_x - slot_x, dest_y - slot_y]

    this_x, this_y = wait_and_record_gui("3) Hover over 'This' submenu", root)
    destroy_this_offsets = [this_x - slot_x, this_y - slot_y]

    pyautogui.click(slot_x, slot_y)
    time.sleep(0.5)

    full = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    popup_roi = draw_roi("5) Draw ROI around the STATS POPUP", full)
    px, py_, pw, ph = popup_roi["x"], popup_roi["y"], popup_roi["w"], popup_roi["h"]
    popup_img = full[py_:py_ + ph, px:px + pw]

    species_roi = draw_roi("6) Draw ROI around SPECIES NAME", popup_img)
    species_roi["x"] += px
    species_roi["y"] += py_

    stat_rois = {}
    for stat in ("health", "stamina", "weight", "melee", "food", "oxygen"):
        r = draw_roi(f"Draw ROI for STAT '{stat}'", popup_img)
        r["x"] += px
        r["y"] += py_
        stat_rois[stat] = r

    hk = simpledialog.askstring("Hotkey", "Enter scan hotkey:", parent=root) or "F8"
    pd = simpledialog.askstring("Popup Delay", "Popup delay sec:", parent=root)
    popup_delay = float(pd) if pd else 0.25
    ad = simpledialog.askstring("Action Delay", "Action delay sec:", parent=root)
    action_delay = float(ad) if ad else 0.05
    debug_mode = messagebox.askyesno("Debug", "Enable debug mode?", parent=root)

    drop_all_button = wait_and_record_gui("10) Hover over 'Drop All Eggs' button", root)

    food_slots = []
    for i in range(1, 4):
        pos = wait_and_record_gui(f"{11 + i}) Hover over FOOD SLOT {i}", root)
        food_slots.append(pos)

    cfg = {
        "slot_x": slot_x,
        "slot_y": slot_y,
        "destroy_offsets": destroy_offsets,
        "destroy_this_offsets": destroy_this_offsets,
        "popup_delay": popup_delay,
        "action_delay": action_delay,
        "hotkey_scan": hk,
        "debug_mode": debug_mode,
        "drop_all_button": drop_all_button,
        "food_slots": food_slots,
        "species_roi": species_roi,
        "stat_rois": stat_rois,
        "ocr": {
            "tesseract_cmd": "tesseract",
            "oem": 3,
            "psm": 7,
        },
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    messagebox.showinfo("Calibration", f"Calibration saved to {SETTINGS_FILE}", parent=root)
    return cfg
