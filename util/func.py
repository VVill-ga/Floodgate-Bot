import discord
import hashlib
import os
import random
import subprocess
import sys

import config

# https://github.com/lohs-software-club/CSClubBot-Python/blob/master/CSClubBot.py#L176
async def send_embed(channel, title, desc=None, color=config.EMBED_DEFAULT):
    if desc is None:
        desc = title
        title = None
    e = discord.Embed(title=title, description=desc, colour=color)
    await channel.send(embed=e)

async def send_success(channel, title, desc=None):
    await send_embed(channel, title, desc, color=config.EMBED_SUCCESS)

async def send_warning(channel, title, desc=None):
    await send_embed(channel, title, desc, color=config.EMBED_WARNING)

async def send_error(channel, title, desc=None):
    await send_embed(channel, title, desc, color=config.EMBED_ERROR)

def generate_token(member):
    return hashlib.md5((str(member.id) + str(random.randint(10000000, 9999999999))).encode()).hexdigest()

# https://github.com/zzzanderw/NFS-Status/blob/master/nfs_status.py#L85
def get_stdout(cmd, timeout=5):
    try:
        result = subprocess.run(cmd.split(" "), stdout=subprocess.PIPE, timeout=timeout)
        return result.stdout.decode("utf-8")
    except subprocess.TimeoutExpired:
        return ""

# https://stackoverflow.com/a/48130152
async def restart_bot(*args):
    os.execl(sys.executable, sys.executable, config.main_path, *args)
    await config.client.close()