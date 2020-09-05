#!/usr/bin/env python3
import discord
import logging
import os
from discord.ext import commands

import config
from util.func import *

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

logger.info("Starting up...")


bot = commands.Bot(command_prefix=config.BOT_PREFIX)


@bot.event
async def on_ready():
    game = discord.Game("CTF")
    await bot.change_presence(status=discord.Status.online, activity=game)
    logger.info("Ready.")

    channel = bot.get_channel(config.BOT_CHANNEL_ID)
    if "restart" in sys.argv:
        await channel.send(embed=info_embed("Bot restarted."))
    if "update" in sys.argv:
        await channel.send(
            embed=info_embed(
                "Bot updated.",
                f'Running commit `{get_stdout("git rev-parse HEAD")[:7]}`',
            )
        )

    # clear arguments
    sys.argv = [sys.argv[0]]


# Load all command extentions
logger.info("Loading commands...")
for filename in os.listdir("./commands"):
    if filename.endswith(".py"):
        logger.info(f"> {filename}")
        bot.load_extension(f"commands.{filename[:-3]}")

# Run bot
if __name__ == "__main__":
    bot.run(config.BOT_TOKEN)
