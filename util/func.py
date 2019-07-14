import discord
import hashlib
import random

import config

# https://github.com/lohs-software-club/CSClubBot-Python/blob/master/CSClubBot.py#L176
async def send_embed_message(msg_channel, msg_title, message, color=config.EMBED_DEFAULT):
    em = discord.Embed(title=msg_title, description=message, colour=color)
    # em.set_author(name='Someone', icon_url=client.user.default_avatar_url)
    await msg_channel.send(embed=em)

def generate_token(member):
    return hashlib.md5((str(member.id) + str(random.randint(10000000, 9999999999))).encode()).hexdigest()