import sys
from unittest.mock import MagicMock
from pyvirtualdisplay import Display
from tkinter import ttk

# stub third-party modules not installed in CI
for mod in ["pyautogui", "keyboard", "cv2", "numpy", "pytesseract"]:
    sys.modules[mod] = MagicMock()

from edit_settings import SettingsEditor, settings

def test_theme_applied_to_widgets():
    settings["theme"] = "clam"
    with Display():
        app = SettingsEditor()
        style = ttk.Style(app)
        assert style.theme_use() == "clam"
        app.destroy()
