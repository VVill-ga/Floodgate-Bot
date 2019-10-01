import discord
import logging
import os
import signal
import sys

from commands import dm, channel, admin
import config
from util import DbWrapper
from util.func import *  # pylint: disable=unused-wildcard-import

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = discord.Client()
config.client = client
db = DbWrapper()

######################
### EVENT HANDLERS ###
######################

@client.event
async def on_ready():
    logger.info('We have logged in as {0.user}'.format(client))

    game = discord.Game("CTF")
    await client.change_presence(status=discord.Status.online, activity=game)

    # get guild and verified role objects so we can add member roles once they are verified
    config.guild = client.get_guild(config.SERVER_ID)
    assert(config.guild is not None)

    config.verified_role = discord.utils.get(config.guild.roles, id=config.VERIFIED_ROLE_ID)
    assert(config.verified_role is not None)

    # get bot channel to provide status updates
    config.bot_channel = discord.utils.get(config.guild.channels, id=config.BOT_CHANNEL_ID)

    if "restart" in sys.argv:
        await send_embed(config.bot_channel, "Bot restarted")
    if "upgrade" in sys.argv:
        await send_embed(config.bot_channel, "Bot upgraded, running commit {}".format(get_stdout("git rev-parse HEAD")[:7]))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # check if we got a DM
    if message.channel.type == discord.ChannelType.private:
        logger.info("got dm from {0.name}#{0.discriminator}: {1}".format(message.author, message.content))
        await dm.handle_dm(message)
    
    else:
        # we aren't in a DM

        # make sure it's a command
        if not message.content.startswith("!"):
            return

        # handle command
        if message.content.startswith("!ping"):
            await channel.ping(message)
        elif message.content.startswith("!yeet"):
            await channel.yeet(message)
        elif message.content.startswith("!roles"):
            await channel.roles(message)
        elif message.content.startswith("!role"):
            await channel.role(message)
        elif message.content.startswith("!help"):
            await channel.help(message)
        elif message.content.startswith("!gitlab"):
            await channel.gitlab(message)
        elif message.content.startswith("!git"):
            await channel.git(message)
        elif message.content.startswith("!cowsay"):
            await channel.cowsay(message)
        elif discord.utils.get(message.author.roles, id=config.ADMIN_ROLE_ID) is not None:
            # admin commands
            if message.content.startswith("!upgrade"):
                await admin.upgrade(message)
            elif message.content.startswith("!restart"):
                await admin.restart(message)
            elif message.content.startswith("!stop"):
                await admin.stop(message)
            elif message.content.startswith("!ctf"):
                await admin.ctf(message)
            else:
                await send_error(message.channel, "Invalid command (!help)")
        else:
            await send_error(message.channel, "Invalid command (!help)")

@client.event
async def on_member_join(member):
    # get confirmation token
    token = generate_token(member)

    # add user to database
    username = "{0.name}#{0.discriminator}".format(member)
    db.new_member(member.id, username, token)

    await member.send("Welcome to the OSU Security Club Discord Server! In order to gain full server access, you'll need to verify your email address. Please send me your Oregon State email address")

config.main_path = os.path.join(os.path.abspath(""), sys.argv[0])
client.run(config.DISCORD_CLIENT_TOKEN)
db.close()
