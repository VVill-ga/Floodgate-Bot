import discord
import textwrap
import sys
import random
import requests
import dateutil.parser
from datetime import datetime
from pytz import timezone

from cowpy import cow

import config
from util.func import *  # pylint: disable=unused-wildcard-import
from util import DbWrapper

db = DbWrapper()

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

async def upcoming(message):
    limit = 5
    headers = {'User-Agent': 'OSUSEC'}
    response = requests.get("https://ctftime.org/api/v1/events/", params={"limit": limit}, headers=headers).json()
    msg = ''
    for i in response:
        msg += '**Name:** ' + i['title'] + '\n'
        start = dateutil.parser.parse(i['start']).astimezone(timezone('US/Pacific'))
        end = dateutil.parser.parse(i['finish']).astimezone(timezone('US/Pacific'))

        msg += '**Start:** ' + start.strftime('%X PST %B %d, %Y') + '\n'
        msg += '**End:** ' + end.strftime('%X PST %B %d, %Y') + '\n'
        msg += '**Online:** ' + ('No' if i['onsite'] else 'Yes') + '\n'
        msg += '**URL:** ' + i['ctftime_url'] + '\n'
        msg += '\n'

    await send_success(message.channel, msg)

async def gitlab(message):
    # validate args
    try:
        gitlab_username = message.content.split(" ")[1]
    except:
        await send_error(message.channel, "GitLab error", "You need to specify a username")
        return

    # check if user already is registered for gitlab
    if db.is_user_gitlab_registered(message.author.id):
        await send_error(message.channel, "GitLab error", "User already registered for GitLab group")
        return

    # make sure user is ctf
    if discord.utils.get(message.author.roles, id=config.VALID_ROLES["CTF"]) is None:
        await send_error(message.channel, "GitLab error", "User doesn't have CTF role")
        return

    # do api stuff
    headers = {
        "Authorization": "Bearer " + config.GITLAB_TOKEN
    }

    # get username
    # https://docs.gitlab.com/ee/api/users.html#for-normal-users
    # parse out id
    response = requests.get("https://gitlab.com/api/v4/users", data={"username": gitlab_username}, headers=headers)

    try:
        user_id = response.json()[0]["id"]
    except:
        await send_error(message.channel, "GitLab error", "Failed to find user with username `{}`".format(gitlab_username))
        return

    # add user to group
    # https://docs.gitlab.com/ee/api/members.html#add-a-member-to-a-group-or-project
    reponse = requests.post("https://gitlab.com/api/v4/groups/{}/members".format(config.GITLAB_GROUP_ID), data={"user_id": user_id, "access_level": 30}, headers=headers)

    if response.status_code != 200:
        await send_error(message.channel, "GitLab error", "Error adding user to group: `{}`".format(response.json()))
        return

    # save to db
    try:
        db.register_user_gitlab(message.author.id, gitlab_username)
    except:
        await send_error(message.channel, "DB error", "Error saving gitlab registration")
        return

    await send_success(message.channel, "GitLab success", "Successfully added `{}` to the GitLab group".format(gitlab_username))

async def cowsay(message):
    try:
        text = " ".join(message.content.split(" ")[1:])
    except:
        await send_error(message.channel, "Need something to cowsay")

    mycow = cow.Small()

    await message.channel.send("```{}```".format(mycow.milk(text)))

async def help(message):
    txt = """\
        Valid commands:
        * `roles`
        * `role`
        * `ping`
        * `yeet`
        * `help`
        * `git`
        * `gitlab`
        * `cowsay`
        * `upcoming`

        Admin commands:
        * `ctf`
        * `upgrade`
        * `restart`
        * `stop`
        """

    await send_embed(message.channel, "Help", textwrap.dedent(txt))

async def cookie(message):
    if (message.content.split(" ")[1:] is not None):
        await send_embed(message.channel, "🍪" + " ".join(message.content.split(" ")[1:]) + " has been sent a cookie!")
