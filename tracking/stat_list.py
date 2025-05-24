from config.config import Config
from utils.logger import get_logger

log = get_logger("stat_list")

def dump_stat_list():
    cfg = Config()
    lines = []
    for sp in sorted(cfg.progress.keys()):
        data = cfg.progress[sp]
        lines.append(f"== {sp} ==")
        lines.append(f"Top stats     : {data.get('top_stats',{})}")
        lines.append(f"Mut thresholds: {data.get('mut_stats',{})}")
        lines.append(f"Stud info     : {data.get('stud',{})}\n")

    with open("stat_list.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info("Wrote stat_list.txt")

if __name__ == "__main__":
    dump_stat_list()
