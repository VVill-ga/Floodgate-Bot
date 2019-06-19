import discord
import logging
import hashlib

from secret import SERVER_ID, VERIFIED_ROLE_ID, DISCORD_CLIENT_TOKEN, generate_token
from util import db, email

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = discord.Client()
db = db.DbWrapper()

server = None
verified_role = None

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    game = discord.Game("CTF")
    await client.change_presence(status=discord.Status.online, activity=game)

    # get server and verified role objects so we can add member roles once they are verified
    global server, verified_role
    # server = discord.utils.get(client.guilds, id=SERVER_ID)
    server = client.get_guild(SERVER_ID)
    assert(server is not None)

    verified_role = discord.utils.get(server.roles, id=VERIFIED_ROLE_ID)
    assert(verified_role is not None)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # check if we got a DM
    if message.channel.type == discord.ChannelType.private:

        # check if user is already verified
        if not db.is_user_verified(message.author.id):

            # user isn't verified, check if their message is a valid OSU email
            if email.is_valid_email(message.content):

                # email is valid, add to DB and send token
                db.set_email(message.author.id, message.content)
                email.send_confirmation(message.content, db.get_token(message.author.id))

                await message.channel.send("I've emailed {} a confirmation token. Please send me that token to get verified!".format(message.content))
            else:

                # message wasn't a valid email
                # maybe it's a token?

                if db.verify_member(message.author.id, message.content) == 1:

                    # this person had that message as their token, they are now verified

                    # TODO add the "Member" role
                    server_member = server.get_member(message.author.id)
                    await server_member.add_roles(verified_role)
                    await message.channel.send("Thank you for verifying. I've updated your roles, and you should be able to get access to all of the channels now.")

                else:

                    # email isn't valid
                    await message.channel.send('Invalid email or token. Make sure to provide your OSU email address')

        print("got dm from {0.name}#{0.discriminator}: {1}".format(message.author, message.content))

    if message.content.startswith('!ping'):
        await message.channel.send('pong')

@client.event
async def on_member_join(member):
    # get confirmation token
    token = generate_token(member)

    # add user to database
    username = "{0.name}#{0.discriminator}".format(member)
    db.new_member(member.id, username, token)

    await member.send("Welcome to the OSU Security Club Discord Server! In order to gain full server access, you'll need to verify your email address. Please send me your Oregon State email address")

client.run(DISCORD_CLIENT_TOKEN)
db.close()