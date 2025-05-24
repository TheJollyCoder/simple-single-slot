from config.config import Config
from utils.logger import get_logger
from difflib import get_close_matches

log = get_logger("tracker")

class ProgressTracker:
    def __init__(self, config: Config):
        self.config = config
        self.progress = config.progress
        self.rules    = config.rules

    def normalize_species(self, raw: str) -> str:
        names = list(self.rules.keys())
        matches = get_close_matches(raw, names, n=1, cutoff=0.6)
        return matches[0] if matches else raw

    def update_top_stats(self, species: str, stats: dict):
        sp = self.normalize_species(species)
        top = self.progress.setdefault(sp, {}).setdefault("top_stats", {})
        for stat, v in stats.items():
            if v["base"] > top.get(stat,0):
                top[stat] = v["base"]

    def update_mutation_thresholds(self, species: str, stats: dict, sex: str):
        if sex!="male": return
        sp = self.normalize_species(species)
        muts = self.progress.setdefault(sp, {}).setdefault("mut_stats", {})
        for stat, v in stats.items():
            if v["mutation"] > muts.get(stat,0):
                muts[stat] = v["mutation"]

    def update_stud(self, species: str, stats: dict, sex: str):
        if sex!="male": return
        sp   = self.normalize_species(species)
        entry = self.progress.setdefault(sp, {})
        studs = entry.setdefault("stud", {})
        top   = entry.get("top_stats",{})
        score = sum(1 for s in stats if stats[s]["base"] >= top.get(s,0))
        if score > studs.get("score", -1):
            studs["stats"] = stats
            studs["score"] = score

    def save(self):
        self.config.save_progress()
