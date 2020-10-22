import asyncio
import dateutil.parser
import discord
import random
import requests
from cowpy import cow
from discord.ext import commands
from pytz import timezone

import config
from util.checks import *
from util.func import *


class ChannelCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong!")

    @commands.command()
    async def git(self, ctx):
        commit = get_stdout("git rev-parse HEAD")[:7]
        url = get_stdout("git remote get-url origin")

        await ctx.send(
            embed=info_embed("Git Info", f"Running commit `{commit}`\nfrom `{url}`")
        )

    @commands.command()
    async def yeet(self, ctx):
        choices = [
            'lyell read says "yote"',
            "https://tenor.com/view/yeet-rafiki-simba-lion-king-gif-12559094",
            "https://tenor.com/view/big-yeet-spinning-gif-11694855",
            "https://tenor.com/view/dab-dancing-idgaf-gif-5661979",
            "https://tenor.com/view/yeet-fortnite-dance-lazerbeem-dance-gif-14816618",
        ]

        await ctx.send(random.choice(choices))

    def get_upcoming(self, count):
        response = requests.get(
            "https://ctftime.org/api/v1/events/",
            params={"limit": count},
            headers={"User-Agent": "OSUSEC Bot v2"},
        ).json()

        # remove non-online events
        return list(filter(lambda i: not i["onsite"], response))

    @commands.command()
    async def upcoming(self, ctx, count: int = 5):
        if count > 12:
            count = 12

        response = self.get_upcoming(count)
        while len(response) < count:
            response = self.get_upcoming(count + count - len(response))

        embed = discord.Embed(title="Upcoming CTFs:", colour=config.EMBED_DEFAULT)
        for idx, i in enumerate(response):
            start = dateutil.parser.parse(i["start"]).astimezone(timezone("US/Pacific"))
            end = dateutil.parser.parse(i["finish"]).astimezone(timezone("US/Pacific"))
            msg = f"""**Start:** {start.strftime("%X PST %B %d, %Y")}
            **End:** {end.strftime("%X PST %B %d, %Y")}
            **CTFtime URL:** [{i["ctftime_url"].split('/')[-2]}]({i["ctftime_url"]})
            \u200b
            """

            embed.add_field(name=i["title"], value=msg, inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def cowsay(self, ctx, *, message=None):
        if message is None or message == "-s":
            return await ctx.send(embed=error_embed("Need something to `cowsay`!"))

        if "`" in message:
            return await ctx.send(
                embed=error_embed("Cowsay escape will not be that easy ;)")
            )

        stoned = message.startswith("-s ")
        if stoned:
            mycow = cow.Small(eyes="stoned", tongue=True)
            message = message[3:]
        else:
            mycow = cow.Small()
        await ctx.send(f"```{mycow.milk(message)}```")

    @commands.command()
    async def cookie(self, ctx, *, message=None):
        if message is not None:
            await ctx.send(embed=info_embed(f"🍪 {message} has been sent a cookie! 🍪"))

    @commands.command(name="ban")
    async def fake_ban(self, ctx):
        if len(ctx.message.mentions) > 0 and has_admin_role(ctx.message.mentions[0]):
            await ctx.send(embed=info_embed(None, "no u"))
        else:
            choices = [
                "https://tenor.com/view/ban-button-keyboard-press-the-ban-button-gif-16387934",
                "https://giphy.com/gifs/hammer-super-mario-8-bit-qPD4yGsrc0pdm",
                "https://giphy.com/gifs/ban-banned-salt-bae-Vh2c84FAPVyvvjZJNM",
            ]

            await ctx.send(random.choice(choices))

    @commands.command()
    @is_verified()
    async def malware(self, ctx):
        message = await ctx.send(
            embed=warning_embed(
                "Are you sure?",
                f"""{ctx.author.mention}, by agreeing to access this channel, you agree \
                to only use the samples within in agreement with the [OSUSEC Code of Ethics](https://www.osusec.org/code-of-ethics/) \
                and the [channel rules](https://docs.google.com/document/d/11rS6Fb5jSCxDWK6nkoBpvlEZNebMGWVOymWltXXcri0/edit?usp=sharing).
                We are not responsible if you infect your own or someone else's computer.
                """,
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
            await ctx.author.add_roles(
                discord.utils.get(ctx.guild.roles, id=config.ROLES["malware"])
            )
            await message.edit(embed=success_embed("Confirmed.", "Don't be evil."))
        else:
            await message.edit(embed=error_embed("~~Are you sure?~~", "Cancelled."))

        await message.clear_reactions()

    @commands.command()
    @is_verified()
    async def politics(self, ctx):
        message = await ctx.send(
            embed=warning_embed(
                "Are you sure?",
                f"""{ctx.author.mention}, by agreeing to access this channel, you agree \
                to participate in accordance with the [OSUSEC Code of Ethics](https://www.osusec.org/code-of-ethics/) \
                and the [channel rules](https://docs.google.com/document/d/1r4DEWnMZAQ4HES5jJN58g3Vhm7Oeory4bmbWHr4RWXo/edit?usp=sharing).
                """,
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
            await ctx.author.add_roles(
                discord.utils.get(ctx.guild.roles, id=config.ROLES["politics"])
            )
            await message.edit(embed=success_embed("Confirmed.", "Please Be Civil."))
        else:
            await message.edit(embed=error_embed("~~Are you sure?~~", "Cancelled."))

        await message.clear_reactions()

    @commands.command()
    @is_verified()
    async def leave(self, ctx, *, message=None):
        if message == "politics":
            if config.ROLES["politics"] in [x.id for x in ctx.author.roles]:
                await ctx.author.remove_roles(
                    discord.utils.get(ctx.guild.roles, id=config.ROLES["politics"])
                )
        elif message == "malware":
            if config.ROLES["malware"] in [x.id for x in ctx.author.roles]:
                await ctx.author.remove_roles(
                    discord.utils.get(ctx.guild.roles, id=config.ROLES["malware"])
                )


def setup(bot):
    bot.add_cog(ChannelCommands(bot))


def teardown(bot):
    bot.remove_cog("ChannelCommands")
