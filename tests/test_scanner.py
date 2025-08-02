import sys
import types

# Provide dummy pyautogui so scanner can import without a display
sys.modules['pyautogui'] = types.SimpleNamespace(onScreen=lambda *a, **k: False)

import scanner


def test_is_invalid_all_zero_stats():
    scan = {
        "species": "CS Test Male",
        "stats": {
            "health": {"base": 0},
            "stamina": {"base": 0},
            "oxygen": {"base": 0},
            "food": {"base": 0},
            "weight": {"base": 0},
            "melee": {"base": 0},
            "speed": {"base": 0},
        },
    }
    assert scanner.is_invalid(scan) is False


def test_scan_once_sets_tesseract_cmd(monkeypatch):
    dummy_pt = types.SimpleNamespace(pytesseract=types.SimpleNamespace())
    monkeypatch.setattr(scanner, "pytesseract", dummy_pt)
    monkeypatch.setattr(scanner.pyautogui, "onScreen", lambda *a, **k: False)
    settings = {"slot_x": 0, "slot_y": 0, "ocr": {"tesseract_cmd": "custom"}}
    scanner.scan_once(settings)
    assert dummy_pt.pytesseract.tesseract_cmd == "custom"

