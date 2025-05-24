import tkinter as tk
from tkinter import messagebox
import os
from tracking.stat_list import dump_stat_list
from config.config import Config

class ToolsTab(tk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        tk.Button(self, text="Generate Stat List", command=self.gen_stat).pack(pady=5)
        tk.Button(self, text="Reload Config",    command=self.reload).pack(pady=5)

    def gen_stat(self):
        try:
            dump_stat_list()
            messagebox.showinfo("Done", "Stat list generated (stat_list.txt).")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate stat list:\n{e}")

    def reload(self):
        try:
            # Recreate Config in place
            self.config = Config(os.path.dirname(self.config.settings_path))
            messagebox.showinfo("Reloaded", "Configuration reloaded.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload config:\n{e}")
