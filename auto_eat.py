import json
import time
import random
import threading
from typing import Optional

import pyautogui

SETTINGS_FILE = "settings.json"


def load_settings() -> dict:
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def eat_food(settings: Optional[dict] = None) -> bool:
    """Double-click one of the configured food slots."""
    settings = settings or load_settings()
    for x, y in settings.get("food_slots", []):
        if pyautogui.onScreen(x, y):
            pyautogui.doubleClick(x, y)
            return True
    return False


def _auto_loop(settings: dict, stop: threading.Event) -> None:
    while not stop.is_set():
        eat_food(settings)
        delay = random.uniform(120, 240)
        for _ in range(int(delay)):
            if stop.is_set():
                break
            time.sleep(1)


def start_auto_eat(settings: Optional[dict] = None) -> threading.Event:
    settings = settings or load_settings()
    stop_event = threading.Event()
    t = threading.Thread(
        target=_auto_loop,
        args=(settings, stop_event),
        daemon=True,
    )
    t.start()
    return stop_event


if __name__ == "__main__":
    stop = start_auto_eat()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop.set()
