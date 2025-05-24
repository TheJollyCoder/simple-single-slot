import os

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

if __name__ == "__main__":
    with open("project_tree.txt", "w") as f:
        print(os.getcwd(), file=f)
        dump_tree(os.getcwd(), out_file=f)
    print("Wrote project_tree.txt")

