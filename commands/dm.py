from discord.ext import commands

import config
from util import DbWrapper, email
from util.func import *

db = DbWrapper()


class DMCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # ignore ourself
        if message.author.bot:
            return

        # if message is DM
        if isinstance(message.channel, discord.channel.DMChannel):
            await self.handle_dm(message)

    async def handle_dm(self, message):
        # check if we got a valid @osu email
        if email.is_valid_email(message.content):
            # email is valid
            # check if its from a verified user
            if db.is_user_verified(message.author.id):
                # email is from verified user
                # check if email is the same, if yes, re-add member
                if db.get_email(message.author.id) == message.content:
                    # email checks out
                    await message.send(
                        embed=info_embed(
                            "This account is already verified, re-adding Member role",
                        )
                    )

                    guild = message.client.get_guild(config.GUILD_ID)
                    member = guild.get_member(message.author.id)
                    await member.add_roles(
                        discord.utils.get(guild.roles, id=config.ROLES["verified"])
                    )
                else:
                    # wrong email
                    await ctx.send(
                        embed=error_embed(
                            "This account was verified with a different email address",
                            "Please provide the original email.",
                        )
                    )
            else:
                # new user, add to DB and send token
                db.set_email(message.author.id, message.content)
                email.send_confirmation(
                    message.content, db.get_token(message.author.id)
                )

                await ctx.send(
                    embed=info_embed(
                        f"Emailed a confirmation token to {message.content}",
                        "Please reply with that token to get verified!",
                    )
                )

        # message wasn't a valid email
        # maybe it's a token?
        elif db.verify_member(message.author.id, message.content) == 1:
            # this person had that message as their token, they are now verified
            guild = message.client.get_guild(config.GUILD_ID)
            member = guild.get_member(message.author.id)
            await member.add_roles(
                discord.utils.get(guild.roles, id=config.ROLES["verified"])
            )

            await ctx.send(
                embbed=success_embed(
                    "Verification successful",
                    f"""Thank you for verifying, `{db.get_email(message.author.id)}`.
                    I've updated your roles, and you should have access to all of the channels now.
                    """,
                )
            )

        # message wasn't a valid token
        else:
            await ctx.send(
                embed=error_embed(
                    "Invalid email or token",
                    "Make sure to provide your OSU email address (`@oregonstate.edu`).",
                )
            )


def setup(bot):
    bot.add_cog(DMCommands(bot))


def teardown(bot):
    bot.remove_cog("DMCommands")
