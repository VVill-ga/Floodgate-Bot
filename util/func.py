import discord
import hashlib
import random

import config

async def send_embed(channel, title, desc=None, color=config.EMBED_DEFAULT):
    e = discord.Embed(title=title, description=desc, colour=color)
    await channel.send(embed=e)

async def send_success(channel, title, desc):
    await send_embed(channel, title, desc, color=config.EMBED_SUCCESS)

async def send_warning(channel, title, desc):
    await send_embed(channel, title, desc, color=config.EMBED_WARNING)

async def send_error(channel, title, desc):
    await send_embed(channel, title, desc, color=config.EMBED_ERROR)

def generate_token(member):
    return hashlib.md5((str(member.id) + str(random.randint(10000000, 9999999999))).encode()).hexdigest()