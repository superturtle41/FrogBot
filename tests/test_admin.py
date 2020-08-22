import pytest
import discord.ext.test as dpytest
from discord.ext.test import backend, get_config, message
import discord.ext.commands as commands
import datetime as dt
import functools
import discord
from dndbot.utils.functions import create_default_embed

pytestmark = pytest.mark.usefixtures('configure')


@pytest.fixture()
def use_dev(configure):
    global dev, devmess
    dev = backend.make_member(
            backend.make_user("DevUser", "0001", id_num=175386962364989440),
            get_config().guilds[0]
        )

    devmess = functools.partial(message, member=dev)


@pytest.mark.asyncio
async def test_stop_unauthorized():
    """
    Testing to make sure the stop command returns unauthorized for non-owner.
    """

    with pytest.raises(commands.errors.CheckFailure):
        await dpytest.message(';stop')
    dpytest.verify_message("You do not have permission to stop the bot!")


@pytest.mark.asyncio
async def test_stop(use_dev):
    """
    Testing to make sure stop command recognizes owner
    """
    await devmess(";stop no")
    dpytest.verify_message("Okay, shutting down...")


@pytest.mark.asyncio
async def test_uptime(configure):
    configure.uptime = dt.datetime.now()
    await dpytest.message(';uptime')
    await dpytest.empty_queue()
