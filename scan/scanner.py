#!/usr/bin/env python3
import time
import cv2
import numpy as np
import pyautogui
from config.config import Config
from ocr_helpers import baseline_up, enhance_and_ocr, normalize_stat_text
from utils.logger import get_logger
from queue import Queue
import threading
import re
import pytesseract

log = get_logger("scanner")
input_queue = Queue()

def _input_worker():
    while True:
        cmd, args = input_queue.get()
        try:
            if cmd == "move":
                pyautogui.moveTo(*args)
            elif cmd == "click":
                pyautogui.click(*args)
            elif cmd == "double_click":
                pyautogui.doubleClick(*args)
            elif cmd == "right_click":
                pyautogui.rightClick(*args)
            elif cmd == "press":
                pyautogui.press(args)
        except Exception:
            log.exception("Input worker error")

threading.Thread(target=_input_worker, daemon=True).start()

def scan_once(config: Config) -> dict | str:
    s = config.settings
    try:
        # open egg slot
        input_queue.put(("move", (s["slot_x"], s["slot_y"])))
        input_queue.put(("click", (s["slot_x"], s["slot_y"], s.get("action_delay",0))))
        time.sleep(s.get("popup_delay",0.25))

        full = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)

        # species OCR
        r = s["species_roi"]
        crop = full[r["y"]:r["y"]+r["h"], r["x"]:r["x"]+r["w"]]
        sp = pytesseract.image_to_string(
            cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY),
            config=f"--oem {s['ocr']['oem']} --psm 7"
        ).splitlines()[0].strip()
        log.debug("Species OCR: %s", sp)
        if not sp or "cs" not in sp.lower():
            return "no_egg"

        stats = {}
        for stat, roi in s["stat_rois"].items():
            crop = full[roi["y"]:roi["y"]+roi["h"], roi["x"]:roi["x"]+roi["w"]]
            prim = baseline_up(crop)
            try:
                txt = pytesseract.image_to_string(
                    cv2.cvtColor(prim,cv2.COLOR_BGR2GRAY),
                    config=f"--oem {s['ocr']['oem']} --psm {s['ocr']['psm']}"
                )
                nums = list(map(int, re.findall(r"\d+", normalize_stat_text(txt))))
                base, mut = nums if len(nums)==2 else (0,0)
            except Exception:
                log.debug("Primary OCR failed for %s, using fallback", stat)
                pairs = []
                for o in enhance_and_ocr(crop):
                    n = re.findall(r"\d+", o)
                    if len(n)==2:
                        pairs.append((int(n[0]), int(n[1])))
                base, mut = max(set(pairs), key=pairs.count) if pairs else (0,0)
            stats[stat] = {"base": base, "mutation": mut}

        return {"species": sp, "stats": stats}

    except Exception:
        log.exception("scan_once error")
        return "no_egg"

def scan_slot(config: Config) -> dict | str:
    try:
        first = scan_once(config)
        if first=="no_egg": return first
        second = scan_once(config)
        if second=="no_egg": return second
        if first==second:
            return first

        # majority vote
        scans = [scan_once(config) for _ in range(3)]
        final = {"species": scans[0]["species"], "stats": {}}
        for stat in scans[0]["stats"]:
            vals = [(r["stats"][stat]["base"],r["stats"][stat]["mutation"]) 
                    for r in scans if r!="no_egg"]
            final["stats"][stat] = {"base":0,"mutation":0}
            if vals:
                final["stats"][stat] = max(set(vals), key=vals.count)
        return final

    except Exception:
        log.exception("scan_slot error")
        return "no_egg"
