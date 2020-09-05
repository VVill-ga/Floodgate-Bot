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
            embed=embed_embed("Git Info", f"Running commit `{commit}`\nfrom `{url}`")
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
    async def fake_ban(self, ctx, member: discord.Member = None):
        if member is None or has_admin_role(member):
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
    async def spicy(self, ctx):
        message = await ctx.send(
            embed=warning_embed(
                "Are you sure?",
                f"""{ctx.author.mention}, by agreeing to access this channel, you agree to only use the \
                samples within in agreement with the OSUSEC Code of Ethics: https://www.osusec.org/code-of-ethics/
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
            spicy_channel = ctx.bot.get_channel(config.MALWARE_CHANNEL_ID)
            perms = spicy_channel.overwrites
            perms[ctx.author] = discord.PermissionOverwrite(view_channel=True)
            await spicy_channel.edit(overwrites=perms)
            await message.edit(embed=success_embed("Confirmed.", "Don't be evil."))
        else:
            await message.edit(embed=error_embed("~~Are you sure?~~", "Cancelled."))

        await message.clear_reactions()


def setup(bot):
    bot.add_cog(ChannelCommands(bot))


def teardown(bot):
    bot.remove_cog("ChannelCommands")
