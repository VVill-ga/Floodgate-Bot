import base64
import io

import asyncio
import discord
from discord.ext import commands
import aiohttp

import config
from util.checks import *
from util.func import *


class CtfCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ctf")
    @is_ctf()
    async def create_ctf(self, ctx, *, ctf_name):
        ctf_category = discord.utils.get(
            ctx.guild.categories, id=config.CTF_CATEGORY_ID
        )

        # assume permissions are set in category
        channel = await ctx.guild.create_text_channel(ctf_name, category=ctf_category)
        await channel.edit(sync_permissions=True)

        await ctx.send(
            embed=success_embed(
                "Channel created.", f"Created new CTF channel: {channel.mention}"
            )
        )

    @create_ctf.error
    async def create_ctf_err(self, ctx, error):
        if isinstance(error, commands.UserInputError):
            await ctx.send(
                embed=error_embed("No name given!", "Usage: `!ctf [ctf name]`")
            )

    @commands.command(name="archive")
    @is_ctf()
    async def archive_ctf(self, ctx):
        # ignore non-ctf-category channels
        if ctx.channel.category_id != config.CTF_CATEGORY_ID:
            return await ctx.send(embed=error_embed("Use me in a ctf channel!"))

        message = await ctx.send(
            embed=warning_embed(
                "Are you sure?", f"This will archive {ctx.channel.mention}."
            )
        )
        await message.add_reaction("❌")
        await message.add_reaction("✅")

        def check(reaction, user):
            return user.id == ctx.author.id and str(reaction.emoji) in ["❌", "✅"]

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", check=check, timeout=30.0
            )
        except asyncio.TimeoutError:
            await message.edit(embed=warning_embed("~~Are you sure?~~", "Timed out."))
            return await message.clear_reactions()

        if str(reaction.emoji) == "✅":
            archive_category = discord.utils.get(
                ctx.guild.categories, id=config.ARCHIVE_CATEGORY_ID
            )

            # delete oldest channel to stay under 50 channel category limit
            oldest_channel = min(
                archive_category.text_channels, key=lambda channel: channel.created_at
            )
            await oldest_channel.delete(reason="oldest channel in archive")

            await ctx.channel.edit(category=archive_category, sync_permissions=False)
            await message.edit(embed=success_embed("Archived."))
            await ctx.channel.edit(sync_permissions=True)
        else:
            await message.edit(embed=error_embed("~~Are you sure?~~", "Cancelled."))

        await message.clear_reactions()

    @commands.command(name="decompile")
    @is_ctf()
    async def decompile(self, ctx):
        # make sure there is an attachment
        if len(ctx.message.attachments) == 0:
            await ctx.send(
                embed=error_embed(
                    "No binary",
                    "You need to upload a binary and put `!decompile` in the message",
                )
            )
            return

        async with aiohttp.ClientSession() as session:
            # download binary
            async with session.get(ctx.message.attachments[0].url) as r:
                if r.status != 200:
                    await ctx.send(
                        embed=error_embed(
                            "Error",
                            f"Failed to download binary, was it deleted? (status code: {r.status})",
                        )
                    )
                    return

                bin_contents = base64.b64encode(await r.content.read()).decode()

                headers = {"Authorization": "Bearer " + config.DAAS_API_KEY}

                # request decomp
                body = {
                    "requestor": f"{ctx.message.author.name}#{ctx.message.author.discriminator} ({ctx.message.author.id})",
                    "binary": bin_contents,
                }
                async with session.post(
                    config.DAAS_URL + "/request_decomp", headers=headers, json=body
                ) as r:
                    resp = await r.json()
                    bin_id = resp["id"]

                    if r.status != 200 or resp["status"] != "ok":
                        await ctx.send(
                            embed=error_embed(
                                "Couldn't decompile",
                                f"Error from server (status code: {r.status}, status: {resp['status']})",
                            )
                        )
                        return

                    message = await ctx.send(
                        embed=warning_embed(
                            "Decompiling...", "Binary is queued for analysis"
                        )
                    )

                    for _ in range(20):
                        # this stuff might break, I'm not entirely sure how all this async stuff works
                        async with session.get(
                            config.DAAS_URL + f"/status/{bin_id}", headers=headers
                        ) as r:
                            ret = await r.json()
                            if ret["analysis_status"] == "completed":
                                await message.edit(
                                    embed=success_embed(
                                        "Decompilation completed",
                                        "Decompilation was successful, retrieving output",
                                    )
                                )
                                break
                            await message.edit(
                                embed=warning_embed(
                                    "Decompiling...",
                                    f"Binary is decompiling\n\nCurrent status: `{ret['analysis_status']}`",
                                )
                            )
                        await asyncio.sleep(1)
                    else:
                        await message.edit(
                            embed=error_embed(
                                "Couldn't decompile", "Decompilation timed out"
                            )
                        )
                        return

                    async with session.get(
                        config.DAAS_URL + f"/get_decompilation/{bin_id}",
                        headers=headers,
                    ) as r:
                        ret = await r.json()

                        output_filename = (
                            f"{ctx.message.attachments[0].filename}_decomp.c"
                        )
                        data = io.BytesIO(base64.b64decode(ret["output"].encode()))

                        await ctx.channel.send(file=discord.File(data, output_filename))
                        await message.edit(
                            embed=success_embed(
                                "Decompilation completed",
                                "Decompilation was successful, see below for output",
                            )
                        )

    @commands.command(name="pin")
    @is_ctf()
    async def pin_message(self, ctx):

        if ctx.channel.category_id != config.CTF_CATEGORY_ID:
            return await ctx.send(
                embed=error_embed(
                    "Use me in a ctf channel!"
                )
            )

        if ctx.message.reference == None:
            return await ctx.send(
                embed=error_embed(
                    "Reply to a message to pin it!"
                )
            )

        to_pin = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        await to_pin.pin()
        await ctx.message.add_reaction("✅")


def setup(bot):
    bot.add_cog(CtfCommands(bot))


def teardown(bot):
    bot.remove_cog("CtfCommands")
