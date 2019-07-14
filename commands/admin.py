import discord

import config
from util.func import *  # pylint: disable=unused-wildcard-import

async def restart(message):
    await send_warning(message.channel, "Restarting bot")
    await restart_bot("restart")

async def upgrade(message):
    await send_embed(message.channel, "Pulling latest version from origin/master (may take a little while)")
    get_stdout("git pull", timeout=20)

    await send_warning(message.channel, "Restarting bot")
    await restart_bot("upgrade")

async def stop(message):
    await send_error(message.channel, "Stopping bot")
    await config.client.close()
    sys.exit(0)

async def ctf(message):
    try:
        name = message.content.split(" ")[1]
    except:
        send_error(message.channel, "Error", "Usage: `!ctf [ctf name]`")
        return

    ctf_category = discord.utils.get(config.guild.categories, name="CTF")
    assert(ctf_category is not None)
    channel = config.guild.create_text_channel(name, category=ctf_category)

    channel.edit(sync_permissions=True, position=2)

    send_success(message.channel, "Channel created", "New CTF channel created: #{}".format(name))
