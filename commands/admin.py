import logging
import os
from discord.ext import commands

from util.checks import *
from util.func import *

logger = logging.getLogger("discord")


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_admin()
    async def restart(self, ctx):
        await ctx.send(embed=warning_embed("Restarting bot..."))
        await restart_bot("restart")

    @commands.command(name="upgrade", aliases=["update"])
    @is_admin()
    async def upgrade(self, ctx):
        await ctx.send(embed=info_embed(f"Updating bot on branch `{get_stdout("git symbolic-ref -q HEAD")}`...", "This may take a bit"))
        logger.info("Updating repo & restarting bot...")
        get_stdout("git pull", timeout=20)
        await ctx.send(embed=warning_embed("Restarting bot..."))
        await restart_bot("update")

    @commands.command(name="stop", aliases=["shutdown"])
    @is_admin()
    async def stop(self, ctx):
        await ctx.send(embed=error_embed("Stopping bot..."))
        await ctx.bot.close()  # stops bot.run()

    @commands.command()
    @is_admin()
    async def reload(self, ctx):
        await ctx.send(embed=warning_embed("Reloading commands..."))
        logger.info("Reloading commands...")
        print("Reloading commands...")

        for filename in os.listdir("./commands"):
            if filename.endswith(".py"):
                logger.info(f"> {filename}")
                print(f"> {filename}")
                ctx.bot.reload_extension(f"commands.{filename[:-3]}")

        await ctx.send(embed=success_embed("Commands reloaded."))


def setup(bot):
    bot.add_cog(AdminCommands(bot))


def teardown(bot):
    bot.remove_cog("AdminCommands")
