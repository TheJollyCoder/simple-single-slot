import json
import tkinter as tk
from tkinter import messagebox

class SpeciesTab(tk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.rules = config.rules
        self.current = None

        # Species list
        self.species_list = tk.Listbox(self, exportselection=False)
        self.species_list.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        for sp in sorted(self.rules.keys()):
            self.species_list.insert("end", sp)
        self.species_list.bind("<<ListboxSelect>>", self.on_select)

        # Details panel
        df = tk.Frame(self)
        df.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        df.columnconfigure(1, weight=1)

        tk.Label(df, text="Modes (comma)").grid(row=0, column=0, sticky="w")
        self.modes_entry = tk.Entry(df)
        self.modes_entry.grid(row=0, column=1, sticky="ew")

        tk.Label(df, text="Mut Stats (comma)").grid(row=1, column=0, sticky="w")
        self.mut_entry = tk.Entry(df)
        self.mut_entry.grid(row=1, column=1, sticky="ew")

        tk.Label(df, text="Top Stats (comma)").grid(row=2, column=0, sticky="w")
        self.top_entry = tk.Entry(df)
        self.top_entry.grid(row=2, column=1, sticky="ew")

        tk.Button(df, text="Save Species", command=self.save_species).grid(
            row=3, column=0, columnspan=2, pady=10
        )

        self.columnconfigure(1, weight=1)

    def on_select(self, event):
        sel = self.species_list.curselection()
        if not sel:
            return
        sp = self.species_list.get(sel[0])
        self.current = sp
        data = self.rules.get(sp, {})
        self.modes_entry.delete(0, "end")
        self.modes_entry.insert(0, ",".join(data.get("modes", [])))
        self.mut_entry.delete(0, "end")
        self.mut_entry.insert(0, ",".join(data.get("mut_stats", [])))
        self.top_entry.delete(0, "end")
        self.top_entry.insert(0, ",".join(data.get("top_stats", [])))

    def save_species(self):
        if not self.current:
            return
        modes = [m.strip() for m in self.modes_entry.get().split(",") if m.strip()]
        mut   = [s.strip() for s in self.mut_entry.get().split(",") if s.strip()]
        top   = [s.strip() for s in self.top_entry.get().split(",") if s.strip()]

        self.rules[self.current]["modes"]    = modes
        self.rules[self.current]["mut_stats"] = mut
        self.rules[self.current]["top_stats"] = top

        try:
            with open(self.config.rules_path, "w", encoding="utf-8") as f:
                json.dump(self.rules, f, indent=2)
            messagebox.showinfo("Saved", f"Configuration for {self.current} saved.")
        except Exception:
            messagebox.showerror("Error", f"Could not save {self.current}.")
