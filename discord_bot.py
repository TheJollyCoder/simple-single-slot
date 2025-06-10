import os
import json
import time
import asyncio
import threading

import discord
from discord.ext import commands
import pyautogui

from auto_eat import eat_food

SETTINGS_FILE = "settings.json"

with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
    SETTINGS = json.load(f)

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN") or SETTINGS.get("bot_token")
if not BOT_TOKEN:
    raise RuntimeError("Bot token not provided via DISCORD_BOT_TOKEN or settings.json")

bot = commands.Bot(command_prefix="!")

# shared lock to prevent simultaneous pyautogui actions
GUI_LOCK = threading.Lock()


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


bot.run(BOT_TOKEN)
