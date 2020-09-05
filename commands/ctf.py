import asyncio
import discord
from discord.ext import commands

import config
from util.checks import *
from util.func import *


class CtfCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ctf")
    @is_ctf()
    async def create_ctf(self, ctx, *, ctf_name):
        ctf_category = discord.utils.get(
            ctx.guild.categories, id=config.CTF_CATEGORY_ID
        )

        # assume permissions are set in category
        channel = await ctx.guild.create_text_channel(ctf_name, category=ctf_category)
        await channel.edit(sync_permissions=True)

        await ctx.send(
            embed=success_embed(
                "Channel created.", f"Created new CTF channel: {channel.mention}"
            )
        )

    @create_ctf.error
    async def create_ctf_err(self, ctx, error):
        if isinstance(error, commands.UserInputError):
            await ctx.send(
                embed=error_embed("No name given!", "Usage: `!ctf [ctf name]`")
            )

    @commands.command(name="archive")
    @is_ctf()
    async def archive_ctf(self, ctx):
        # ignore non-ctf-category channels
        if ctx.channel.category_id != config.CTF_CATEGORY_ID:
            return

        message = await ctx.send(
            embed=warning_embed(
                "Are you sure?", f"This will archive {ctx.channel.mention}."
            )
        )
        await message.add_reaction("❌")
        await message.add_reaction("✅")

        def check(reaction, user):
            return user.id == ctx.author.id and str(reaction.emoji) in ["❌", "✅"]

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", check=check, timeout=30.0
            )
        except asyncio.TimeoutError:
            await message.edit(embed=warning_embed("~~Are you sure?~~", "Timed out."))
            return await message.clear_reactions()

        if str(reaction.emoji) == "✅":
            archive_category = discord.utils.get(
                ctx.guild.categories, id=config.ARCHIVE_CATEGORY_ID
            )
            await ctx.channel.edit(category=archive_category, sync_permissions=False)
            await message.edit(embed=success_embed("Archived."))
            await ctx.channel.edit(sync_permissions=True)
        else:
            await message.edit(embed=error_embed("~~Are you sure?~~", "Cancelled."))

        await message.clear_reactions()


def setup(bot):
    bot.add_cog(CtfCommands(bot))


def teardown(bot):
    bot.remove_cog("CtfCommands")
