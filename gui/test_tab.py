import tkinter as tk
from tkinter import scrolledtext

from scan.scanner import scan_slot
from config.config import Config

class TestTab(tk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        tk.Button(self, text="Test Single Scan", command=self.test_scan).pack(pady=5)
        self.output = scrolledtext.ScrolledText(self, height=10)
        self.output.pack(fill="both", expand=True, padx=5, pady=5)

    def test_scan(self):
        result = scan_slot(self.config)
        self.output.delete("1.0", "end")
        self.output.insert("end", f"{result}")
