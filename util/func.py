import asyncio
import discord
import hashlib
import os
import random
import subprocess
import sys

import config


def info_embed(title, desc=False, color=config.EMBED_DEFAULT):
    d = {"type": "rich", "title": title, "color": color}
    if desc:
        d["description"] = desc
    return discord.Embed.from_dict(d)


def success_embed(title, desc=False):
    return info_embed(title, desc, color=config.EMBED_SUCCESS)


def warning_embed(title, desc=False):
    return info_embed(title, desc, color=config.EMBED_WARNING)


def error_embed(title, desc=False):
    return info_embed(title, desc, color=config.EMBED_ERROR)


def generate_token(member):
    return hashlib.md5(
        (str(member.id) + str(random.randint(10000000, 9999999999))).encode()
    ).hexdigest()


# https://github.com/zzzanderw/NFS-Status/blob/master/nfs_status.py#L85
def get_stdout(cmd, timeout=5):
    try:
        result = subprocess.run(cmd.split(" "), stdout=subprocess.PIPE, timeout=timeout)
        return result.stdout.decode("utf-8")
    except subprocess.TimeoutExpired:
        return ""


# https://stackoverflow.com/a/48130152
def restart_bot(*args):
    path_to_main_file = os.path.abspath(__file__).replace("util/func.py", "bot.py")
    os.execl(sys.executable, sys.executable, path_to_main_file, *args)


async def aws_wait_until(instance, state):
    # poll instance instead of blocking `instance.wait_until_terminated()`
    # to allow websocket to continue
    while instance.state["Name"] != state:
        await asyncio.sleep(1)
        instance.reload()
