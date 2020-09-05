import discord
from discord.ext import commands

import config


def has_role(member, role_id):
    return discord.utils.get(member.roles, id=role_id) is not None


def is_verified():
    async def predicate(ctx):
        return has_role(ctx.author, config.ROLES["verified"])

    return commands.check(predicate)


def is_admin():
    async def predicate(ctx):
        return has_role(ctx.author, config.ROLES["admin"])

    return commands.check(predicate)


def is_ctf():
    async def predicate(ctx):
        return has_role(ctx.author, config.ROLES["ctf"])

    return commands.check(predicate)
