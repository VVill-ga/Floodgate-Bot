import logging

import config
from util import DbWrapper, email

db = DbWrapper()

async def handle_dm(message):
    # check if we got a valid @osu email
    if email.is_valid_email(message.content):
        # email is valid
        # check if its from a verified user
        if db.is_user_verified(message.author.id):
            # email is from verified user
            # check if email is the same, if yes, re-add member
            if db.get_email(message.author.id) == message.content:
                # email checks out
                await message.channel.send("This accout is already verified, re-adding Member role")
                server_member = config.server.get_member(message.author.id)
                await server_member.add_roles(config.verified_role)
            else:
                # wrong email
                await message.channel.send("This account was verified with a different email address. Please provide the proper email")
        else:
            # new user, add to DB and send token
            db.set_email(message.author.id, message.content)
            email.send_confirmation(message.content, db.get_token(message.author.id))

            await message.channel.send("I've emailed {} a confirmation token. Please send me that token to get verified!".format(message.content))
    # message wasn't a valid email
    # maybe it's a token?
    elif db.verify_member(message.author.id, message.content) == 1:
        # this person had that message as their token, they are now verified
        server_member = config.server.get_member(message.author.id)
        await server_member.add_roles(config.verified_role)

        await message.channel.send("Thank you for verifying. I've updated your roles, and you should be able to get access to all of the channels now.")
    # message wasn't a valid token
    else:
        await message.channel.send('Invalid email or token. Make sure to provide your OSU email address')
            