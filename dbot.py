import datetime as datetime
import logging
import sys

import discord
from discord.ext import commands
from pymongo import MongoClient

import bot_config as config
from utils.functions import try_delete

COGS = (
    'cogs.util', 'cogs.eval', 'cogs.admin', 'cogs.error_handeling',
    'cogs.quest_roles', 'cogs.dm_commands'
)


def get_prefix(client, message):
    if not message.guild:
        return commands.when_mentioned_or(config.PREFIX)(client, message)
    guild_id = str(message.guild.id)
    if guild_id in client.prefixes:
        prefix = client.prefixes.get(guild_id, config.PREFIX)
    else:
        dbsearch = client.mdb['prefixes'].find_one({'guild_id': guild_id})
        if dbsearch is not None:
            prefix = dbsearch.get('prefix', config.PREFIX)
        else:
            prefix = config.PREFIX
        client.prefixes[guild_id] = prefix
    return commands.when_mentioned_or(prefix)(client, message)


class FrogBot(commands.Bot):

    def __init__(self, command_prefix=get_prefix, desc: str = '', **options):
        self.launch_time = datetime.datetime.utcnow()
        self._dev_id = config.DEV_ID
        self._prefix = config.PREFIX
        self.mongo_client = MongoClient(config.MONGO_URL)
        self.mdb = self.mongo_client[config.MONGO_DB]
        self.muted = set()
        self.prefixes = dict()
        super(FrogBot, self).__init__(command_prefix, description=desc,
                                      activity=self.update_status_from_db(), **options)
        self.update_muted_from_db()

    @property
    def uptime(self):
        """Returns the current uptime of the bot"""
        return datetime.datetime.utcnow() - self.launch_time

    @property
    def owner(self):
        return self._dev_id

    @property
    def prefix(self):
        return self._prefix

    def update_status_from_db(self):
        current_status = self.mdb['bot_settings'].find_one({'setting': 'status'})
        if current_status is None:
            current_status = f'{config.DEFAULT_STATUS} | {config.PREFIX}help'
        else:
            current_status = f'{current_status["status"]} | {config.PREFIX}help'
        activity = discord.Game(name=current_status)
        return activity

    def update_muted_from_db(self):
        muted = []
        for muted_user in self.mdb['muted_clients'].find():
            muted.append(muted_user['_id'])
        self.muted = muted
        return muted


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

    bot.ready_time = datetime.datetime.utcnow()

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


@bot.event
async def on_guild_join(joined):
    # Check to make sure we aren't approaching
    if len(bot.guilds) > 90:
        if joined.system_channel:
            await joined.system_channel.send('Until I am verified, I cannot join any more servers.')
        await joined.leave()


for cog in COGS:
    bot.load_extension(cog)

if __name__ == '__main__':
    bot.mdb['authorized'].update_one({'_id': bot.owner}, {'$set': {'_id': bot.owner}}, upsert=True)
    bot.run(config.TOKEN)
