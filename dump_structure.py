import os
from pathlib import Path
from logger import get_logger

log = get_logger("dump_structure")

def dump_tree(root, indent="", out_file=None):
    entries = sorted(os.listdir(root))
    for i, name in enumerate(entries):
        path = os.path.join(root, name)
        connector = "└── " if i == len(entries)-1 else "├── "
        line = f"{indent}{connector}{name}"
        print(line, file=out_file)
        if os.path.isdir(path):
            extension = "    " if i == len(entries)-1 else "│   "
            dump_tree(path, indent + extension, out_file)

BASE_DIR = Path(__file__).resolve().parent

if __name__ == "__main__":
    outfile = BASE_DIR / "project_tree.txt"
    with outfile.open("w", encoding="utf-8") as f:
        print(os.getcwd(), file=f)
        dump_tree(os.getcwd(), out_file=f)
    log.info("Wrote project_tree.txt")

