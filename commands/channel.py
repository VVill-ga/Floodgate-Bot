import discord
import textwrap
import sys
import random

import config
from util.func import *  # pylint: disable=unused-wildcard-import

#####################
### USER COMMANDS ###
#####################

async def ping(message):
    await send_embed(message.channel, "Pong!")

async def role(message):
    try:
        split = message.content.split(" ")
        action = split[1]
    except:
        await send_error(message.channel, "Invalid `role` command", "Usage: `role [action] [name]`\nValid actions:\n* `add`\n* `remove`\n\nUse `!roles` to see available roles")
        return

    # make sure we have a valid command
    if action not in ["add", "remove"]:
        await send_error(message.channel, "Invalid `role` command", "Valid commands are `add` and `remove`.")
    else:

        # make sure user is verified
        if discord.utils.get(message.author.roles, id=config.VERIFIED_ROLE_ID) is None:
            # user isn't verified
            await send_error(message.channel, "User isn't verified", "Please verify before requesting roles")
            return

        # user is verified
        role_name = " ".join(split[2:])

        # make sure requested role is valid
        if role_name in config.VALID_ROLES:
            if action == "add":
                await message.author.add_roles(discord.utils.get(config.guild.roles, id=config.VALID_ROLES[role_name]))
                await send_success(message.channel, "Added role")
            elif action == "remove":
                await message.author.remove_roles(discord.utils.get(config.guild.roles, id=config.VALID_ROLES[role_name]))
                await send_success(message.channel, "Removed role")

async def roles(message):
    await send_embed(message.channel, "Valid roles for OSU Security Club", "\n".join(list(config.VALID_ROLES.keys())))

async def git(message):
    commit = get_stdout("git rev-parse HEAD")[:7]
    url = get_stdout("git remote get-url origin")

    await send_embed(message.channel, "Git Info", "Running commit {} from {}".format(commit, url))

async def yeet(message):
    choices = [
        "lyell read says \"yote\"",
        "https://tenor.com/view/yeet-rafiki-simba-lion-king-gif-12559094",
        "https://tenor.com/view/big-yeet-spinning-gif-11694855",
        "https://tenor.com/view/dab-dancing-idgaf-gif-5661979",
        "https://tenor.com/view/yeet-fortnite-dance-lazerbeem-dance-gif-14816618"
    ]

    msg = random.choice(choices)

    await message.channel.send(msg)

async def help(message):
    txt = """\
        Valid commands:
        * `roles`
        * `role`
        * `ping`
        * `yeet`
        * `help`
        * `git`

        Admin commands:
        * `ctf`
        * `upgrade`
        * `restart`
        * `stop`
        """
    
    await send_embed(message.channel, "Help", textwrap.dedent(txt))
