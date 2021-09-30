import discord
import aiohttp
from discord.ext import commands

import config
from util.checks import *
from util.func import *
from util import DbWrapper

db = DbWrapper()


class MemberCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="role", aliases=["getrole", "addrole"])
    @is_verified()
    async def role(self, ctx, action, *, role):
        if action not in ["add", "remove"]:
            return await ctx.send(
                embed=error_embed(
                    "Invalid command",
                    "Usage:\n`!role add [role]`\n`!role remove [role]`",
                )
            )

        role = role.lower()

        # if role is malware or politics, run those functions.
        if role in ["malware", "politics"]:
            command = self.bot.get_command(role)
            return await command.__call__(ctx)

        # if not a valid role
        if role not in config.ALLOWED_ROLES:
            return await ctx.send(
                embed=error_embed(
                    "Invalid role",
                    "Valid roles:\n`" + "`\n`".join(config.ALLOWED_ROLES) + "`",
                )
            )

        if action == "add":
            await ctx.author.add_roles(
                discord.utils.get(ctx.guild.roles, id=config.ROLES[role])
            )
        else:  # remove
            await ctx.author.remove_roles(
                discord.utils.get(ctx.guild.roles, id=config.ROLES[role])
            )

        await ctx.message.add_reaction("✅")

    @role.error
    async def role_err(self, ctx, error):
        # if user is not verified
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(
                embed=error_embed(
                    "User not verified",
                    "Please verify yourself before requesting a role!",
                )
            )

        await ctx.send(
            embed=error_embed(
                "Invalid command",
                "Usage:\n`!role add [role]`\n`!role remove [role]`",
            )
        )

    @commands.command()
    async def roles(self, ctx):
        await ctx.send(
            embed=info_embed(
                "Valid roles for OSUSEC:",
                "`" + "`\n`".join(config.ALLOWED_ROLES) + "`",
            )
        )

    @is_verified()
    @commands.command()
    async def gitlab(self, ctx, username=None):
        if username is None:
            await ctx.send(embed=error_embed("You need to specify a username"))
            return

        # check if user already is registered for gitlab
        if db.is_user_gitlab_registered(ctx.author.id):
            await ctx.send(
                embed=error_embed("User already registered for GitLab group")
            )
            return

        # do api stuff
        headers = {"Authorization": "Bearer " + config.GITLAB_TOKEN}

        # get username
        # https://docs.gitlab.com/ee/api/users.html#for-normal-users
        # parse out id
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://gitlab.com/api/v4/users",
                data={"username": username},
                headers=headers,
            ) as response:
                try:
                    user_id = (await response.json())[0]["id"]
                except:
                    await ctx.send(
                        embed=error_embed(
                            f"Failed to find user with username `{username}`"
                        )
                    )
                    return

            # add user to group
            # https://docs.gitlab.com/ee/api/members.html#add-a-member-to-a-group-or-project
            async with session.post(
                f"https://gitlab.com/api/v4/groups/{config.GITLAB_GROUP_ID}/members",
                data={"user_id": user_id, "access_level": 30},
                headers=headers,
            ) as response:
                if response.status >= 400:
                    await ctx.send(
                        embed=error_embed(
                            f"Error adding user to group:\n```{await response.json()}```"
                        )
                    )
                    return

        # save to db
        try:
            db.register_user_gitlab(ctx.author.id, username)
        except:
            await ctx.send(embed=error_embed("Error saving Gitlab registration to db"))
            return

        await ctx.send(
            embed=success_embed(f"Successfully added `{username}` to the GitLab group")
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # get confirmation token
        token = generate_token(member)

        # add user to database
        db.new_member(member.id, f"{member.name}#{member.discriminator}", token)

        await member.send(
            embed=info_embed(
                "Welcome to the OSU Security Club Discord Server!",
                """In order to gain full server access, you'll need to verify your email.
            Reply with your `@oregonstate.edu` email address, and I'll send you an email with a confirmation code.""",
            )
        )
        # goto dm.py

    @commands.command()
    async def alumni(self, ctx):
        if db.is_user_verified(ctx.message.author.id):
            # Member, remove member, add alumni, react
            await ctx.author.add_roles(
                discord.utils.get(ctx.guild.roles, id=config.ROLES["alumni"])
            )
            await ctx.author.remove_roles(
                discord.utils.get(ctx.guild.roles, id=config.ROLES["verified"])
            )
            await ctx.message.add_reaction("✅")
        else:
            return await ctx.send(embed=error_embed("You are not a member."))


def setup(bot):
    bot.add_cog(MemberCommands(bot))


def teardown(bot):
    bot.remove_cog("MemberCommands")
