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

## Monitored Scan

The `settings.json` file includes a `monitored_scan` option. When enabled, the live
scan loop pauses upon encountering a species not listed in `rules.json` and asks
which modes and stats to track. The chosen configuration is saved and scanning
resumes. If disabled, new species are added automatically using the default
species template without interrupting the loop. The setting can be toggled from
the Global tab of the settings editor.

## Discord Bot

`discord_bot.py` implements a small Discord bot that can control the game and report breeding progress. Set your bot token in `settings.json` under the `bot_token` key or provide it via the `DISCORD_BOT_TOKEN` environment variable. Start the bot with:

```bash
python discord_bot.py
```

Once running you can use commands like `!dropall`, `!eatfood`, and `!progress <species>` in your Discord channel. The Progress tab will also use this token when sending summaries.
