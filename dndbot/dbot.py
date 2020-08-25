import datetime as datetime
import logging
import sys
import traceback

import bot_config as config
import discord
import pymongo
from discord.ext import commands
from utils.checks import NotAuthorized
from utils.functions import try_delete

description = "WIP Economy bot for personal discord server"
COGS = ['cogs.admin', 'cogs.help', 'cogs.repl', 'cogs.roles', 'cogs.channels']


def get_prefix(client, message):
    prefix = [config.prefix]
    return commands.when_mentioned_or(*prefix)(client, message)


class DnDBot(commands.Bot):

    DEV_ID = 175386962364989440

    def __init__(self, command_prefix=get_prefix, desc=description, **options):
        super(DnDBot, self).__init__(command_prefix, descrirption=desc, **options)
        self.launch_time = datetime.datetime.now()
        self.db = pymongo.MongoClient(host=config.mongo_host, username=config.mongo_user, password=config.mongo_pass, authSource=config.mongo_db)
        self.mdb = self.db[config.mongo_db]
        self.version = config.version

    @property
    def uptime(self):
        """Returns the current uptime of the bot"""
        return datetime.datetime.now() - self.launch_time

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.CommandOnCooldown):
            return

        elif isinstance(error, commands.CheckFailure):
            msg = str(error) or "You are not allowed to run this command."
            return await ctx.send(f"Error: {msg}")

        elif isinstance(error, commands.MissingRequiredArgument):
            msg = str(error) or "Missing Unknown Required Argument"
            return await ctx.send(f"Error: {msg}")

        elif isinstance(error, commands.CommandInvokeError):
            msg = str(error) or "Command raised an exception."
            return await ctx.send(f"Error: {msg}")
        elif isinstance(error, NotAuthorized):
            await ctx.send('You are not authorized to use this command.')
        log.warning("Error caused by message: `{}`".format(ctx.message.content))
        for line in traceback.format_exception(type(error), error, error.__traceback__):
            log.warning(line)


log_formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
log = logging.getLogger('bot')

bot = DnDBot(case_insensitive=True)


@bot.event
async def on_ready():
    status = discord.Game(f'D&D | {config.prefix}help')
    await bot.change_presence(activity=status)
    bot.remove_command('help')
    for cog in COGS:
        bot.load_extension(cog)
    log.info(f'>> {bot.user.name} Launched! <<')
    log.info(f'>> Current Cogs: <<')
    log.info(f'>> {", ".join(bot.cogs)} <<')
    log.info(f'>> ID: f{bot.user.id} | Prefix: {config.prefix} <<')
    if config.testing:
        log.info('Bot is in testing mode')
    return


@bot.event
async def on_command(ctx):
    if ctx.command.name == 'eval':
        return
    await try_delete(ctx.message)


if __name__ == "__main__":
    bot.run(config.token, reconnect=True, bot=True)
