import sys
import types
import numpy as np
import os

# Ensure project root on path for importing scanner when tests executed from subdirectory
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


# Provide dummy pyautogui so scanner can import without a display
def _dummy_screenshot(region=None):
    w = region[2] if region else 1
    h = region[3] if region else 1
    return np.zeros((h, w, 3), dtype=np.uint8)


sys.modules['pyautogui'] = types.SimpleNamespace(
    onScreen=lambda *a, **k: False,
    screenshot=_dummy_screenshot,
    moveTo=lambda *a, **k: None,
    click=lambda *a, **k: None,
)

# Minimal stub of cv2 to avoid heavy dependencies during import
sys.modules.setdefault('cv2', types.SimpleNamespace())

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

