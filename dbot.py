import datetime as datetime
import logging
import sys
import traceback

import discord
from discord.ext import commands
from pymongo import MongoClient

import bot_config as config
from utils.functions import try_delete

COGS = (
    'cogs.util', 'cogs.eval', 'cogs.admin',
    'cogs.quest_roles'
)


def get_prefix(client, message):
    prefix = [config.PREFIX]
    return commands.when_mentioned_or(*prefix)(client, message)


class FrogBot(commands.Bot):

    def __init__(self, command_prefix=get_prefix, desc: str = '', **options):
        super(FrogBot, self).__init__(command_prefix, description=desc, **options)
        self.launch_time = datetime.datetime.now()
        self._dev_id = config.DEV_ID
        self._prefix = config.PREFIX
        self.mongo_client = MongoClient(config.MONGO_URL)
        self.mdb = self.mongo_client[config.MONGO_DB]
        self.muted = []

    @property
    def uptime(self):
        """Returns the current uptime of the bot"""
        return datetime.datetime.now() - self.launch_time

    @property
    def owner(self):
        return self._dev_id

    @property
    def prefix(self):
        return self._prefix

    async def update_status_from_db(self):
        current_status = self.mdb['bot_settings'].find_one({'setting': 'status'})
        if current_status is None:
            current_status = f'{config.DEFAULT_STATUS} | {config.PREFIX}help'
        else:
            current_status = f'{current_status["status"]} | {config.PREFIX}help'
        activity = discord.Game(name=current_status)
        await self.change_presence(activity=activity)

    def update_muted_from_db(self):
        muted = []
        for muted_user in self.mdb['muted_clients'].find():
            muted.append(muted_user['_id'])
        self.muted = muted
        return muted

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.CheckFailure):
            msg = str(error) or "You are not allowed to run this command."
            return await ctx.send(f"Error: {msg}")

        elif isinstance(error, commands.MissingRequiredArgument):
            msg = str(error) or "Missing Unknown Required Argument"
            return await ctx.send(f"Error: {msg}")

        error_message = f'An unhandled error has occurred!\n' \
                        f'Please contact the Bot Developer with this message!\n' \
                        f'(Right Click -> Copy Message ID)' \
                        f'{str(error)}\n'

        await ctx.send(error_message)

        log.warning("Error caused by message: `{}`".format(ctx.message.content))
        for line in traceback.format_exception(type(error), error, error.__traceback__):
            log.warning(line)


intents = discord.Intents(
    guilds=True, members=True, messages=True, reactions=True,
    bans=False, emojis=False, integrations=False, webhooks=False, invites=False, voice_states=False, presences=False,
    typing=False
)

bot = FrogBot(desc='Personal Bot written by Dr Turtle', intents=intents,
              allowed_mentions=discord.AllowedMentions.none())

log_formatter = logging.Formatter('%(levelname)s | %(name)s: %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
log = logging.getLogger('bot')


@bot.event
async def on_ready():

    bot.update_muted_from_db()
    await bot.update_status_from_db()

    ready_message = f'\n---------------------------------------------------\n' \
                    f'Bot Ready!\n' \
                    f'Logged in as {bot.user.name} (ID: {bot.user.id})\n' \
                    f'Current Prefix: {config.PREFIX}\n' \
                    f'Loaded {len(bot.muted)} muted users.\n' \
                    f'---------------------------------------------------'
    log.info(ready_message)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in bot.muted:
        return

    await bot.process_commands(message)


@bot.event
async def on_command(ctx):
    if ctx.command.name == 'eval':
        return

    await try_delete(ctx.message)

for cog in COGS:
    bot.load_extension(cog)

if __name__ == '__main__':
    bot.mdb['authorized'].update_one({'_id': bot.owner}, {'$set': {'_id': bot.owner}}, upsert=True)
    bot.run(config.TOKEN)
