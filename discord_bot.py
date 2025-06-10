import os
import json
import time
import asyncio

import discord
from discord.ext import commands
import pyautogui

from commands.user_panel import UserPanelView

from auto_eat import eat_food

SETTINGS_FILE = "settings.json"

with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
    SETTINGS = json.load(f)

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN") or SETTINGS.get("bot_token")
if not BOT_TOKEN:
    raise RuntimeError(
        "Bot token not provided via DISCORD_BOT_TOKEN or settings.json"
    )

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


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
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


@bot.command()
async def dropall(ctx):
    """Drop all eggs using configured coordinates."""
    drop_all(SETTINGS)
    await ctx.send("🗑 Drop All executed")


@bot.command()
async def eatfood(ctx):
    """Consume food from the configured slots."""
    eat_food(SETTINGS)
    await ctx.send("🍗 Ate one food item")


@bot.tree.command(name="user")
async def user_panel(interaction: discord.Interaction):
    """Open the user panel."""
    view = UserPanelView()
    await interaction.response.send_message(embed=view.embed, view=view, ephemeral=True)


bot.run(BOT_TOKEN)
