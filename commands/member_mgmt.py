import discord
import aiohttp
import paramiko
import shlex
import configparser
from discord.ext import commands

import config
from util.checks import *
from util.func import *
from util import DbWrapper

db = DbWrapper()


class MemberCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # get confirmation token
        token = generate_token(member)

        # add user to database
        db.new_member(member.id, f"{member.name}#{member.discriminator}", token)

        await member.send(
            embed=info_embed(
                "Welcome to the RHA/Area Council Discord Server!",
                """In order to gain full server access, you'll need to verify your email.
            Reply with your `ONID@oregonstate.edu` email address, and I'll send you an email with a confirmation code.""",
            )
        )
        # goto dm.py

def setup(bot):
    bot.add_cog(MemberCommands(bot))


def teardown(bot):
    bot.remove_cog("MemberCommands")
