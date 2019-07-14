import discord

import config
from util.func import *  # pylint: disable=unused-wildcard-import

async def ping(message):
    await send_embed(message.channel, "Pong!")

async def role(message):
    split = message.content.split(" ")
    action = split[1]

    # make sure we have a valid command
    if action not in ["add", "remove"]:
        await message.channel.send("Invalid role command. Valid commands are `add` and `remove`.")
    else:

        # make sure user is verified
        if discord.utils.get(message.author.roles, id=config.VERIFIED_ROLE_ID) is not None:

            # user is verified
            role_name = " ".join(split[2:])

            # make sure requested role is valid
            if role_name in config.VALID_ROLES:
                await message.author.add_roles(discord.utils.get(config.server.roles, id=config.VALID_ROLES[role_name]))
                await message.channel.send("Added role")
        else:

            # user isn't verified
            await message.channel.send("User isn't verified. Please verify before requesting roles")

async def roles(message):
    await send_embed(message.channel, "Valid roles for OSU Security Club", "\n".join(list(config.VALID_ROLES.keys())))