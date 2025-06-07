from unittest.mock import MagicMock
import importlib
import sys

def test_theme_applied(monkeypatch):
    monkeypatch.setitem(sys.modules, 'pyautogui', MagicMock())
    monkeypatch.setitem(sys.modules, 'keyboard', MagicMock())
    monkeypatch.setitem(sys.modules, 'cv2', MagicMock())
    monkeypatch.setitem(sys.modules, 'numpy', MagicMock())
    monkeypatch.setitem(sys.modules, 'scanner', MagicMock())
    monkeypatch.setitem(sys.modules, 'breeding_logic', MagicMock())
    monkeypatch.setitem(sys.modules, 'progress_tracker', MagicMock())
    edit_settings = importlib.import_module('edit_settings')
    # patch tkinter root methods to avoid display requirement
    monkeypatch.setattr(edit_settings.tk.Tk, '__init__', lambda self: None)
    monkeypatch.setattr(edit_settings.tk.Tk, 'title', lambda self, *_: None)
    monkeypatch.setattr(edit_settings.tk.Tk, 'geometry', lambda self, *_: None)
    # avoid side effects during init
    monkeypatch.setattr(edit_settings.SettingsEditor, 'create_tabs', lambda self: None)
    monkeypatch.setattr(edit_settings.SettingsEditor, 'update_hotkeys', lambda self, initial=False: None)
    monkeypatch.setattr(edit_settings.messagebox, 'showwarning', lambda *a, **k: None)
    # avoid StringVar requiring real root
    monkeypatch.setattr(edit_settings.tk, 'StringVar', lambda *a, **k: MagicMock())
    monkeypatch.setattr(edit_settings.tk, 'BooleanVar', lambda *a, **k: MagicMock())
    monkeypatch.setattr(edit_settings.tk, 'DoubleVar', lambda *a, **k: MagicMock())

    style_mock = MagicMock()
    monkeypatch.setattr(edit_settings.ttk, 'Style', lambda: style_mock)
    edit_settings.settings['theme'] = 'clam'
    app = edit_settings.SettingsEditor()
    style_mock.theme_use.assert_called_with('clam')
