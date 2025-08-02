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

## OCR Configuration

The scanner uses [PyTesseract](https://pypi.org/project/pytesseract/) for optical character
recognition. If the `tesseract` executable is not on your `PATH`, set the
`ocr.tesseract_cmd` option in `settings.json` to point to it. `scanner.scan_once`
copies this value to `pytesseract.pytesseract.tesseract_cmd` before performing
any OCR calls.

## Main Scripts

- **`edit_settings.py`** – Tkinter GUI for editing configuration and viewing a summary of tracked stats.
- **`scanner.py`** – Uses OCR with PyTesseract to read dino stats from screenshots.
- **`auto_eat.py`** – Periodically double‑clicks configured food slots to keep your creatures fed.
- **`setup_positions.py`** – Interactive helper to record screen coordinates and regions of interest.
- **`dump_structure.py`** – Writes a text representation of the repository tree for debugging.

Other modules implement breeding logic and progress tracking used by these scripts.

## Discord Bot

`discord_bot.py` implements a small Discord bot that can control the game and report breeding progress. Set your bot token in `settings.json` under the `bot_token` key or provide it via the `DISCORD_BOT_TOKEN` environment variable. Start the bot with:

```bash
python discord_bot.py
```

Once running you can use commands like `!dropall`, `!eatfood`, and `!progress <species>` in your Discord channel. The Progress tab will also use this token when sending summaries.
