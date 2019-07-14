import discord
import logging
import hashlib
import random

from commands import dm, channel
import config
from util import DbWrapper
from util.func import *  # pylint: disable=unused-wildcard-import

logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger('discord')
# logger.setLevel(logging.INFO)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)

client = discord.Client()
db = DbWrapper()

######################
### EVENT HANDLERS ###
######################

@client.event
async def on_ready():
    logging.info('We have logged in as {0.user}'.format(client))

    game = discord.Game("CTF")
    await client.change_presence(status=discord.Status.online, activity=game)

    # get server and verified role objects so we can add member roles once they are verified
    config.server = client.get_guild(config.SERVER_ID)
    assert(config.server is not None)

    config.verified_role = discord.utils.get(config.server.roles, id=config.VERIFIED_ROLE_ID)
    assert(config.verified_role is not None)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # check if we got a DM
    if message.channel.type == discord.ChannelType.private:
        logging.info("got dm from {0.name}#{0.discriminator}: {1}".format(message.author, message.content))
        await dm.handle_dm(message)
    
    else:
        # we aren't in a DM

        # make sure it's a command
        if not message.content.startswith("!"):
            return

        # handle command
        if message.content.startswith("!ping"):
            await channel.ping(message)
        elif message.content.startswith("!role "):
            await channel.role(message)
        elif message.content.startswith("!roles"):
            await channel.roles(message)
        elif message.content.startswith("!help"):
            pass
        else:
            await message.channel.send("Invalid command (!help)")

@client.event
async def on_member_join(member):
    # get confirmation token
    token = generate_token(member)

    # add user to database
    username = "{0.name}#{0.discriminator}".format(member)
    db.new_member(member.id, username, token)

    await member.send("Welcome to the OSU Security Club Discord Server! In order to gain full server access, you'll need to verify your email address. Please send me your Oregon State email address")

client.run(config.DISCORD_CLIENT_TOKEN)
db.close()