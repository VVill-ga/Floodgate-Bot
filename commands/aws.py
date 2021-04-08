import asyncio
import boto3
import botocore.exceptions
import logging
from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks

import config_aws
from util.checks import *
from util.func import *

logger = logging.getLogger("discord")

ec2 = boto3.resource("ec2")


class AwsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stale_instance_check.start()

    def cog_unload(self):
        self.stale_instance_check.cancel()

    def get_user_keys(self, user_id):
        # find all non-terminated bot instances requested by user
        return list(
            ec2.key_pairs.filter(
                Filters=[
                    {  # only get bot-created instances
                        "Name": "tag:bot-key",
                        "Values": ["yes"],
                    },
                    {  # instance requested by bot
                        "Name": "tag:requestor-id",
                        "Values": [str(user_id)],
                    },
                ]
            )
        )

    def get_user_instances(self, user_id):
        # find all non-terminated bot instances requested by user
        return list(
            ec2.instances.filter(
                Filters=[
                    {  # ignore already terminated instances
                        "Name": "instance-state-name",
                        "Values": [
                            "pending",
                            "running",
                            "shutting-down",
                            "stopping",
                            "stopped",
                        ],
                    },
                    {  # only get bot-created instances
                        "Name": "tag:bot-instance",
                        "Values": ["yes"],
                    },
                    {  # instance requested by bot
                        "Name": "tag:requestor-id",
                        "Values": [str(user_id)],
                    },
                ]
            )
        )

    def get_bot_instances(self):
        return list(
            ec2.instances.filter(
                Filters=[
                    {  # ignore already terminated instances
                        "Name": "instance-state-name",
                        "Values": [
                            "pending",
                            "running",
                            "shutting-down",
                            "stopping",
                            "stopped",
                        ],
                    },
                    {  # only get bot-created instances
                        "Name": "tag:bot-instance",
                        "Values": ["yes"],
                    },
                ]
            )
        )

    @commands.group()
    @is_aws()
    async def aws(self, ctx):
        if ctx.invoked_subcommand is None:
            help_embed = info_embed("AWS Commands:")
            help_embed.add_field(
                name="!aws", value="Show this help message", inline=False
            )
            help_embed.add_field(
                name="!aws list",
                value="List all of your running instances",
                inline=False,
            )
            help_embed.add_field(
                name="!aws pubkey",
                value="Add an SSH public key to access created instances with",
                inline=False,
            )
            help_embed.add_field(
                name="!aws create <size>",
                value="Spin up a new instance of the specified size",
                inline=False,
            )
            help_embed.add_field(
                name="!aws destroy",
                value="Terminate all of your running instances",
                inline=False,
            )
            await ctx.send(embed=help_embed)

    @aws.command(name="list", aliases=["ls", "show"])
    async def list_instances(self, ctx):
        instances = self.get_user_instances(ctx.author.id)
        now = datetime.now(timezone.utc)

        desc = ""
        for instance in instances:
            instance_age = now - instance.launch_time
            desc += (
                f"`ubuntu@{instance.public_ip_address}` (**{instance.instance_type}**) - {instance.state['Name']}"
                + f"\n(created {round(instance_age.total_seconds() / 3600, 1)}h ago)\n\n"
            )

        if len(instances) == 0:
            desc = "(none)"

        await ctx.send(embed=info_embed("Your instances:", desc))

    @aws.command(name="pubkey", aliases=["addkey", "setkey", "key"])
    async def pubkey(self, ctx, *, key=None):
        if key is None:
            return await ctx.send(
                embed=error_embed(
                    "No key given", "Usage: `!aws pubkey ssh-rsa KEYSTRING...`"
                ),
            )

        # overwrite any existing key
        existing_keys = self.get_user_keys(ctx.author.id)
        if len(existing_keys) != 0:
            await ctx.send(
                embed=warning_embed("Key already exists, replacing with new key..."),
            )
            for k in existing_keys:
                k.delete()

        try:
            key_info = ec2.import_key_pair(
                KeyName=f"botkey-{ctx.author.id}",
                # PublicKeyMaterial=base64.b64encode(bytes(openssl_key, "utf8")),
                PublicKeyMaterial=key,
                TagSpecifications=[
                    {
                        "ResourceType": "key-pair",
                        "Tags": [
                            {"Key": "requestor-id", "Value": str(ctx.author.id)},
                            {"Key": "bot-key", "Value": "yes"},
                        ],
                    },
                ],
            )
        except botocore.exceptions.ClientError:
            return await ctx.send(
                embed=error_embed(
                    "Key is not valid",
                    "Public keys should be in the format:"
                    + "\n```\nssh-rsa AAAASOMELONGSTRINGOFSTUFF= comment\n```",
                ),
            )

        return await ctx.send(
            embed=success_embed(
                "Pubkey successfully imported",
                f"MD5 Fingerprint: `{key_info.key_fingerprint}`",
            )
        )

    @aws.command(name="create", aliases=["up", "spinup", "start"])
    async def create(self, ctx, instance_type=None):

        # has user added a pubkey?
        if len(self.get_user_keys(ctx.author.id)) == 0:
            return await ctx.send(
                embed=error_embed(
                    "No pubkey found", "Add your pubkey with `!aws pubkey <publickey>`"
                ),
            )

        if instance_type not in config_aws.AWS_VALID_INSTANCES:
            return await ctx.send(
                embed=error_embed(
                    "Incorrect instance type",
                    "Valid instances:\n`"
                    + "`\n`".join(config_aws.AWS_VALID_INSTANCES)
                    + "`",
                )
            )

        # does user already have instances?
        instances = self.get_user_instances(ctx.author.id)

        if len(instances) != 0:
            size = instances[0].instance_type
            ip = instances[0].public_ip_address
            return await ctx.send(
                embed=error_embed(
                    "Instance already running",
                    f"You already have a **{size}** instance running at `ubuntu@{ip}`"
                    + "\nPlease terminate it before spinning up a new one!",
                )
            )

        await ctx.message.add_reaction("⌛")

        with open("aws-cloud-config.yml", "r") as cloud_config_file:
            cloud_config = cloud_config_file.read()
            cloud_config = cloud_config.replace("ssh-rsa ADMINKEY admin", config_aws.AWS_ADMIN_PUBKEY)

            instance = ec2.create_instances(
                InstanceType=instance_type,
                ImageId=config_aws.AWS_AMI_ID,
                KeyName=f"botkey-{ctx.author.id}",
                MinCount=1,
                MaxCount=1,
                InstanceInitiatedShutdownBehavior="terminate",
                SecurityGroupIds=[config_aws.AWS_NET_SECURITY_GROUP],
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {
                                "Key": "Name",
                                "Value": f"{ctx.channel.name}-{ctx.author.name}",
                            },
                            {
                                "Key": "bot-instance",
                                "Value": "yes",
                            },
                            {"Key": "requestor-id", "Value": str(ctx.author.id)},
                            {
                                "Key": "stale-last-warned",
                                "Value": f"{datetime.now(timezone.utc)}",
                            },
                        ],
                    }
                ],
                UserData=cloud_config,
            )[0]

        # poll instance instead of blocking `instance.wait_until_running()`
        # to allow websocket to continue
        await aws_wait_until(instance, "running")

        await ctx.message.clear_reaction("⌛")

        creation_embed = success_embed(
            "Instance created",
            f"**{instance.instance_type}** instance created at `ubuntu@{instance.public_ip_address}`",
        )
        creation_embed.add_field(
            name="Note: the tool bootstrap script will still be running",
            value="It will create `~/init-setup-done` once finished",
            inline=False,
        )

        await ctx.send(reference=ctx.message, mention_author=True, embed=creation_embed)

    @aws.command(name="destroy", aliases=["down", "delete", "remove"])
    async def destroy(self, ctx):

        instances = self.get_user_instances(ctx.author.id)

        if len(instances) == 0:
            await ctx.send(embed=warning_embed("No instances found"))
            return

        await ctx.message.add_reaction("⌛")

        for i in instances:
            i.terminate()
            await aws_wait_until(i, "terminated")

        await ctx.message.clear_reaction("⌛")
        await ctx.send(
            reference=ctx.message,
            mention_author=True,
            embed=success_embed(
                "Instances deleted",
                "All of your instances have been removed.",
            ),
        )

    # intermittent task to check for any running instances
    @tasks.loop(hours=config_aws.AWS_STALE_CHECK_INTERVAL)
    async def stale_instance_check(self):
        logger.info("Checking for stale instances...")

        all_instances = self.get_bot_instances()
        now = datetime.now(timezone.utc)

        for i in all_instances:
            last_warned_str = [
                x["Value"] for x in i.tags if x["Key"] == "stale-last-warned"
            ][0]
            last_warned = datetime.fromisoformat(last_warned_str)

            instance_age = now - last_warned

            # if stale and has not been previously warned
            if instance_age > timedelta(hours=config_aws.AWS_STALE_WARN_AGE):
                logger.info(f"> Stale instance {i.id} found, DMing requestor")

                req_id = [x["Value"] for x in i.tags if x["Key"] == "requestor-id"][0]
                requestor = await self.bot.fetch_user(req_id)

                warn_msg = await requestor.send(
                    embed=warning_embed(
                        "Stale instance warning",
                        f"You have had a **{i.instance_type}** instance running for over "
                        + f"{config_aws.AWS_STALE_WARN_AGE}h ({round(instance_age.total_seconds() / 3600, 1)}h)."
                        + "\nReact with ✅ to keep the instance running or ❌ to delete it.",
                    )
                )

                await warn_msg.add_reaction("✅")
                await warn_msg.add_reaction("❌")

                # wait for user to react
                def check(reaction, user):
                    return str(user.id) == str(req_id) and str(reaction.emoji) in [
                        "❌",
                        "✅",
                    ]

                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add",
                        check=check,
                        # wait for specified check cycles
                        timeout=config_aws.AWS_STALE_CHECK_INTERVAL
                        * config_aws.AWS_STALE_DELETE_AFTER
                        * 3600,
                    )
                except asyncio.TimeoutError:
                    await warn_msg.edit(
                        embed=error_embed(
                            "~~Stale instance warning~~",
                            f"""**Timed out, instance deleted**
                            You have had a **{i.instance_type}** instance running for over\
                            {config_aws.AWS_STALE_WARN_AGE}h ({round(instance_age.total_seconds() / 3600, 1)}h).
                            ~~React with ✅ to keep the instance running or ❌ to delete it.~~""",
                        )
                    )
                    await warn_msg.remove_reaction("✅", self.bot.user)
                    await warn_msg.remove_reaction("❌", self.bot.user)
                    i.terminate()
                    return

                if str(reaction.emoji) == "✅":  # keep instance
                    # set last warned tag to current time
                    i.create_tags(
                        Tags=[
                            {"Key": "stale-last-warned", "Value": f"{now}"},
                        ]
                    )
                    await warn_msg.edit(
                        embed=success_embed(
                            "~~Stale instance warning~~", "Keeping instance up."
                        )
                    )

                else:  # destroy instance
                    i.terminate()
                    await warn_msg.edit(
                        embed=error_embed(
                            "~~Stale instance warning~~", "Terminating instance..."
                        )
                    )
                    await aws_wait_until(i, "terminated")
                    await warn_msg.edit(
                        embed=error_embed(
                            "~~Stale instance warning~~", "Instance terminated."
                        )
                    )

                await warn_msg.remove_reaction("✅", self.bot.user)
                await warn_msg.remove_reaction("❌", self.bot.user)

    @aws.command(name="stale")
    @is_admin()
    async def stale(self, ctx):
        # manually run stale instance check
        await self.stale_instance_check.__call__()


def setup(bot):
    bot.add_cog(AwsCommands(bot))


def teardown(bot):
    bot.remove_cog("AwsCommands")
