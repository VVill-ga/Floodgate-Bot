import discord
from discord.ext import commands

import config


def has_role(member, role_id):
    return discord.utils.get(member.roles, id=role_id) is not None


def has_admin_role(member):
    return any(has_role(member, role) for role in config.ROLES['admin'])


def is_verified():
    async def predicate(ctx):
        return has_role(ctx.author, config.ROLES["verified"])

    return commands.check(predicate)


def is_admin():
    async def predicate(ctx):
        return has_admin_role(ctx.author)

    return commands.check(predicate)


def is_ctf():
    async def predicate(ctx):
        return has_role(ctx.author, config.ROLES["ctf"])

    return commands.check(predicate)
