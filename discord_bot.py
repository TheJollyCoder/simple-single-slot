import os
import json
import time
import asyncio
import threading
import urllib.request

import discord
from discord.ext import commands
import pyautogui

from auto_eat import eat_food
from progress_tracker import load_progress

SETTINGS_FILE = "settings.json"

with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
    SETTINGS = json.load(f)

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN") or SETTINGS.get("bot_token")
if not BOT_TOKEN:
    raise RuntimeError("Bot token not provided via DISCORD_BOT_TOKEN or settings.json")

CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

bot = commands.Bot(command_prefix="!")

# shared lock to prevent simultaneous pyautogui actions
GUI_LOCK = threading.Lock()


def build_progress_message(species: str) -> str:
    """Return a formatted breeding progress summary for ``species``."""
    prog = load_progress(SETTINGS.get("current_wipe", "default")).get(species, {})
    lines = [f"{species} stats:"]
    lines.append(f"Females: {prog.get('female_count', 0)}")
    lines.append("Top Stats:")
    for st, val in prog.get("top_stats", {}).items():
        lines.append(f"  {st}: {val}")
    lines.append("Mutation Thresholds:")
    for st, val in prog.get("mutation_thresholds", {}).items():
        lines.append(f"  {st}: {val}")
    return "\n".join(lines)


def send_progress_message(message: str) -> None:
    """Send ``message`` to the configured Discord channel using the bot token."""
    if not CHANNEL_ID:
        raise RuntimeError("DISCORD_CHANNEL_ID not set")
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=json.dumps({"content": message}).encode("utf-8"), headers=headers)
    urllib.request.urlopen(req)


def drop_all(settings):
    """Click the configured drop-all button and confirm."""
    bx, by = settings.get("drop_all_button", [0, 0])
    cx, cy = settings.get("drop_all_confirm", [0, 0])
    pyautogui.moveTo(bx, by)
    pyautogui.click()
    time.sleep(0.5)
    pyautogui.moveTo(cx, cy)
    pyautogui.click()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def dropall(ctx):
    """Drop all eggs using configured coordinates."""
    with GUI_LOCK:
        drop_all(SETTINGS)
    await ctx.send("🗑 Drop All executed")


@bot.command()
async def eatfood(ctx):
    """Consume food from the configured slots."""
    with GUI_LOCK:
        eat_food(SETTINGS)
    await ctx.send("🍗 Ate one food item")


@bot.command()
async def progress(ctx, *, species: str):
    """Send breeding progress summary for ``species``."""
    msg = build_progress_message(species)
    await ctx.send(msg)


bot.run(BOT_TOKEN)
