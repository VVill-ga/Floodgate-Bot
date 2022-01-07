import discord
import aiohttp
import paramiko
import ipaddress
import base64
import shlex
import configparser
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

    @gitlab.error
    async def gitlab_err(self, ctx, error):
        # if user is not verified
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(
                embed=error_embed(
                    "User not verified",
                    "Please verify yourself before requesting to join gitlab!",
                )
            )

        await ctx.send(
            embed=error_embed(
                "Invalid command",
                "Usage:\n`!gitlab <username>`",
            )
        )

    @is_verified()
    @is_cdc()
    @commands.command()
    async def vpn(self, ctx, pubkey=None):
        if pubkey is None:
            return await ctx.send(
                embed=error_embed(
                    "Missing Public Key",
                    "Please specify a wireguard public key.\n```\n!vpn pubkeygoeshere\n```",
                )
            )

        # Check that the supplied public key is valid base64, forbidding invalid chars
        try:
            base64.b64decode(pubkey)
        except:
            return await ctx.send(
                embed=error_embed(
                    "Invalid Public Key",
                    "Please specify a valid wireguard public key.\n```\n!vpn pubkeygoeshere\n```",
                )
            )

        # Establish an SSH Connection to the CDC VPN machine
        # https://stackoverflow.com/questions/3586106/perform-commands-over-ssh-with-python

        ssh = paramiko.SSHClient()

        key = paramiko.RSAKey.from_private_key_file(config.CDC_VPN_PRIVATE_KEY_PATH)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=config.CDC_VPN_IP, username=config.CDC_VPN_USERNAME, pkey=key
        )

        # get last configured entry to calculate next free ip
        _, ssh_stdout, _ = ssh.exec_command("sudo tail -n 5 /etc/wireguard/wg0.conf")

        # use ini parser to get last ip from conf
        wgconf = configparser.ConfigParser()
        try:
            wgconf.read_string(ssh_stdout.read().decode("utf-8"))
            last_config_ip = wgconf["Peer"]["AllowedIPs"]
        except Exception as e:
            print(f"Issue in parsing VPN Config: {str(e)}")
            return await ctx.send(
                embed=error_embed(
                    "Could not parse server VPN configuration",
                    "Please contact an officer.",
                )
            )

        last_ip = ipaddress.ip_address(last_config_ip.split("/32")[0])

        if not last_ip + 1 in ipaddress.ip_network("10.1.2.0/24"):
            return await ctx.send(
                embed=error_embed(
                    "No more IPs available for VPN peers",
                    "Please contact an officer.",
                )
            )

        # We are now good to add the user's pubkey to the wireguard network config
        # on the vpn host, followed by printing the client config they should use
        allowed_ip = last_ip + 1
        user = self.bot.get_user(ctx.author.id)
        new_conf_entry = "\n".join(
            [
                "",
                f"# {user.display_name}#{user.discriminator}",
                "[Peer]",
                "Endpoint = 0.0.0.0:13337",
                f"AllowedIPs = {allowed_ip}/32",
                f"PublicKey = {pubkey}",
            ]
        )

        # We have to write with echo as the file is root-owned
        ssh.exec_command(
            f"echo {shlex.quote(new_conf_entry)} | sudo tee -a /etc/wireguard/wg0.conf"
        )

        # Run sudo systemctl restart wg-quick@wg0
        ssh.exec_command("sudo systemctl restart wg-quick@wg0")

        ssh.close()

        await ctx.send(
            embed=success_embed(
                f"Key Added Successfully.",
                "\n".join(
                    [
                        "**Enter the following in your local config:**",
                        "```ini",
                        "[Interface]",
                        "PrivateKey = <your private key here>",
                        "ListenPort = 13337",
                        f"Address = {allowed_ip}/32",
                        "DNS = 10.1.20.198",
                        "",
                        "[Peer]",
                        f"PublicKey = {config.CDC_VPN_SERVER_PUBKEY}",
                        "AllowedIPs = 10.1.1.0/24, 10.1.0.0/24, 10.1.20.0/24",
                        f"Endpoint = {config.CDC_VPN_IP}:13337",
                        "```",
                    ]
                ),
            )
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
