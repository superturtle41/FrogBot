import pytest
import discord.ext.test as dpytest


@pytest.fixture()
async def configure():
    from dndbot.dbot import DnDBot, COGS

    bot = DnDBot()
    bot.remove_command('help')
    for cog in COGS:
        bot.load_extension('dndbot.'+cog)

    dpytest.configure(bot, 1, 1, 10)
    config = dpytest.get_config()

    yield bot
