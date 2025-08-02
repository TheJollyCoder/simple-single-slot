#!/usr/bin/env python3
import os
import re
import time
from collections import Counter

from logger import get_logger
log = get_logger("scanner")

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover - handled via OCR_AVAILABLE
    cv2 = None
    log.warning("OpenCV (cv2) not available; scanning disabled.")

import numpy as np

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - handled via OCR_AVAILABLE
    pytesseract = None
    log.warning("pytesseract not available; scanning disabled.")

import pyautogui

OCR_AVAILABLE = cv2 is not None and pytesseract is not None
if not OCR_AVAILABLE:
    log.warning("OCR libraries missing. Scanning features will be unavailable.")

def normalize_stat_text(text: str) -> str:
    """Cleanup OCR text for numeric parsing."""
    # Many fonts cause Tesseract to misread ``l``/``I``/``|`` as ``1``.  We
    # normalise those here *before* attempting to parse numbers.
    text = text.strip()
    text = text.replace("l", "1").replace("|", "1").replace("I", "1").replace("i", "1")
    # Sometimes a stray 1 appears next to punctuation or whitespace.  If it's
    # not adjacent to other digits we treat it as noise and strip it.
    text = re.sub(r"(?<!\d)1(?!\d)", "", text)
    text = re.sub(r"(?<=\d)[lI|i]", "1", text)
    log.debug(f"normalize_stat_text → {text!r}")
    return text

def baseline_up(img):
    h, w = img.shape[:2]
    up = cv2.resize(img, (w*3, h*3), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)

def enhance_and_ocr(image: np.ndarray, runs: int = 3) -> list:
    """
    Main + Extra-3 fallback:
    Upscale→Sharpen→Otsu→Adaptive Mean Threshold→OCR (multiple runs)
    """
    scale = 4
    up = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharp = cv2.filter2D(gray, -1, kernel)
    _, otsu = cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        otsu, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    cfg = "--psm 7 -c tessedit_char_whitelist=0123456789()l|"
    results = []
    for i in range(runs):
        raw = pytesseract.image_to_string(adaptive, config=cfg).strip()
        norm = normalize_stat_text(raw)
        log.debug(f"[enhance_and_ocr] Run {i+1} → raw: {raw!r} | normalized: {norm!r}")
        results.append(norm)
    return results

def ocr_number(img, oem, psm):
    """
    Primary OCR pass: Otsu→Tesseract→normalize→extract digits.
    If text ends with ')' but only a single digit inside, treat as failure → return (None,0).
    Only split out base+mut when there are at least two digits before the ')'.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cfg = f"--oem {oem} --psm {psm} -c tessedit_char_whitelist=0123456789()l|"
    raw = pytesseract.image_to_string(bw, config=cfg)
    log.debug("OCR raw text: %r", raw)
    text = normalize_stat_text(raw)
    log.debug("OCR normalized text: %r", text)

    # handle "512)" → base=51, mut=2
    m = re.match(r"^(\d+)\)$", text)
    if m:
        digits = m.group(1)
        if len(digits) >= 2:
            base, mut = int(digits[:-1]), int(digits[-1])
            log.debug("ocr_number combined-case → base=%r, mut=%r", base, mut)
            return base, mut
        else:
            # lone digit + stray ')' → signal fallback
            log.debug("ocr_number lone-digit parenthesis → triggering fallback")
            return None, 0

    nums = re.findall(r"\d+", text)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    if len(nums) == 1:
        return int(nums[0]), 0
    return None, 0

def scan_once(settings, debug=False):
    log.debug("scan_once: start")
    if not OCR_AVAILABLE:
        log.error("scan_once called but OCR libraries are unavailable")
        return "ocr_unavailable"
    x, y = settings["slot_x"], settings["slot_y"]
    if not pyautogui.onScreen(x, y):
        log.warning("Slot off-screen, skipping scan.")
        return "no_egg"

    pyautogui.moveTo(x, y)
    pyautogui.click(x, y, interval=settings.get("action_delay", 0.0))
    time.sleep(settings.get("popup_delay", 0.0))
    log.debug("Clicked slot at (%d,%d)", x, y)

    # Calculate the bounding rectangle containing the species ROI and all stat ROIs
    sx, sy, sw, sh = settings["species_roi"].values()
    bounds = [
        (sx, sy, sx + sw, sy + sh),
    ]
    for roi in settings["stat_rois"].values():
        x0, y0, w0, h0 = roi.values()
        bounds.append((x0, y0, x0 + w0, y0 + h0))

    min_x = min(b[0] for b in bounds)
    min_y = min(b[1] for b in bounds)
    max_x = max(b[2] for b in bounds)
    max_y = max(b[3] for b in bounds)

    region = (min_x, min_y, max_x - min_x, max_y - min_y)
    full = cv2.cvtColor(
        np.array(pyautogui.screenshot(region=region)), cv2.COLOR_RGB2BGR
    )

    # Species OCR
    sx, sy, sw, sh = settings["species_roi"].values()
    sx -= min_x
    sy -= min_y
    crop_sp = full[sy:sy+sh, sx:sx+sw]
    sp_txt = pytesseract.image_to_string(
        cv2.cvtColor(crop_sp, cv2.COLOR_BGR2GRAY),
        config=f"--oem {settings['ocr']['oem']} --psm 7"
    )
    species = sp_txt.splitlines()[0].strip() if sp_txt.splitlines() else ""
    log.debug("Species OCR: %r", species)
      # ─── Invalid‐species guard: must read “CS” and “male”/“female” ─────────
    sl = species.lower()
    if "cs" not in sl or not ("male" in sl or "female" in sl):
        log.info(f"Invalid species OCR ({species!r}), skipping slot")
        return "no_egg"
    # Stat OCR
    stats = {}
    for stat, roi in settings["stat_rois"].items():
        x0, y0, w0, h0 = roi.values()
        x0 -= min_x
        y0 -= min_y
        crop = full[y0:y0+h0, x0:x0+w0]

        prim = baseline_up(crop)
        b, m = ocr_number(prim, settings["ocr"]["oem"], settings["ocr"]["psm"])
        log.debug("%s primary → base=%r, mut=%r", stat, b, m)

        # Fallback if missing or suspiciously low
        parsed = []
        if stat != "speed" and (b is None or b <= 10):
            log.debug("%s → enhance_and_ocr fallback", stat)
            enhanced = enhance_and_ocr(crop, runs=3)
            log.debug("%s enhanced texts → %r", stat, enhanced)
            for txt in enhanced:
                cleaned = normalize_stat_text(txt)
                mutation_match = re.search(r"\((\d{1,2})\)", cleaned)
                nums = re.findall(r"\d+", cleaned)

                base, mut = None, 0
                if len(nums) >= 2:
                    base, mut = int(nums[0]), int(nums[1])
                elif len(nums) == 1:
                    rawnum = nums[0]
                    mut = int(mutation_match.group(1)) if mutation_match else 0
                    # jammed-case fallback: "512)"
                    if mut == 0 and len(rawnum) >= 3:
                        try:
                            bc, mc = int(rawnum[:-1]), int(rawnum[-1])
                            if bc <= 99:
                                base, mut = bc, mc
                            else:
                                base, mut = int(rawnum), 0
                        except:
                            base, mut = int(rawnum), 0
                    else:
                        base = int(rawnum)

                if base is not None:
                    parsed.append((base, mut))

            if parsed:
                (b, m), _ = Counter(parsed).most_common(1)[0]
                log.debug("%s fallback chosen → base=%r, mut=%r", stat, b, m)

        stats[stat] = {"base": 0 if b is None else b, "mutation": 0 if m is None else m}

    return {"species": species, "stats": stats}

def is_invalid(scan):
    """Return True when OCR produced obviously bogus values."""
    # Values of 0 are legitimate, so we only guard against excessively
    # large numbers which indicate an OCR failure.
    too_big = any(v["base"] > 99 for v in scan["stats"].values())
    return too_big

def scan_slot(settings, debug=False):
    """OCR a single slot with validation and optional re-scans."""
    if not OCR_AVAILABLE:
        log.error("scan_slot called but OCR libraries are unavailable")
        return "ocr_unavailable"

    result = scan_once(settings, debug)
    if result in ("no_egg", "ocr_unavailable"):
        return result

    if not is_invalid(result):
        return result

    log.warning("Initial scan invalid; performing additional passes")
    batch = [scan_once(settings, debug) for _ in range(3)]
    if any(x == "no_egg" for x in batch):
        return "no_egg"

    final = {"species": batch[0]["species"], "stats": {}}
    for stat in batch[0]["stats"]:
        vals = [
            (r["stats"][stat]["base"], r["stats"][stat]["mutation"]) for r in batch
        ]
        best = max(set(vals), key=vals.count)
        final["stats"][stat] = {"base": best[0], "mutation": best[1]}

    if is_invalid(final):
        log.warning("Rescans still produced invalid data; treating as no egg")
        return "no_egg"
    return final
