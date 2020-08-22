import discord
from discord.ext import commands
import bot_config as config
import logging
import sys
from datetime import datetime
import pymongo
from utils.checks import NotAuthorized

description = "WIP Economy bot for personal discord server"
COGS = ['cogs.admin', 'cogs.help', 'cogs.repl', 'cogs.roles', 'cogs.channels']


def get_prefix(client, message):
    prefix = [config.prefix]
    return commands.when_mentioned_or(*prefix)(client, message)


class DnDBot(commands.Bot):

    DEV_ID = 175386962364989440

    def __init__(self, command_prefix=get_prefix, desc=description, **options):
        super(DnDBot, self).__init__(command_prefix, descrirption=desc, **options)
        self.db = pymongo.MongoClient(host=config.mongo_host, username=config.mongo_user, password=config.mongo_pass, authSource=config.mongo_db)
        self.mdb = self.db[config.mongo_db]


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
    bot.uptime = datetime.now()
    for cog in COGS:
        log.debug('Loading Cog: '+cog)
        try:
            bot.load_extension(cog)
        except:
            log.error('Error Loading Cog '+cog)
            exit(1)
        log.debug('Loaded Cog: '+cog)
    log.info(f'Logged in as {bot.user.name} - {bot.user.id}')
    if config.testing:
        log.info('Bot is in testing mode')
    return


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        log.debug("Command Error: Command not found.")
        return
    elif isinstance(error, commands.CommandOnCooldown):
        log.debug(f"Command Error: Command on Cooldown | {error}")
        return
    elif isinstance(error, NotAuthorized):
        await ctx.send('You are not authorized to use this command.')
    else:
        log.error(error)

if __name__ == "__main__":
    bot.run(config.token, reconnect=True, bot=True)
