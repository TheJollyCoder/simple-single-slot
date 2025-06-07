# Simple Single Slot Breeding Tools

This repository contains a few utilities that automate breeding tasks in a single slot setup.

## Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Tests require a virtual display when run in headless environments. Install `Xvfb` if your system does not have a display:

```bash
sudo apt-get install xvfb
```

## Running Tests

Execute all unit tests with:

```bash
pytest
```

## Main Scripts

- **`edit_settings.py`** – Tkinter GUI for editing configuration and viewing a summary of tracked stats.
- **`scanner.py`** – Uses OCR with PyTesseract to read dino stats from screenshots.
- **`auto_eat.py`** – Periodically double‑clicks configured food slots to keep your creatures fed.
- **`setup_positions.py`** – Interactive helper to record screen coordinates and regions of interest.
- **`dump_structure.py`** – Writes a text representation of the repository tree for debugging.

Other modules implement breeding logic and progress tracking used by these scripts.
