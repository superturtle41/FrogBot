import datetime as datetime
import logging
import sys

import discord
import motor.motor_asyncio
from discord.ext import commands, tasks

import bot_config as config
from utils.context import Context as CustomContext
from utils.functions import try_delete

import sentry_sdk

COGS = (
    'cogs.util', 'jishaku', 'cogs.admin', 'cogs.error_handeling', 'cogs.info',
    'cogs.custom_commands', 'cogs.keep_alive',
    'cogs.quest_roles', 'cogs.dm_commands', 'cogs.sheet_approval',
    'cogs.help'
)


async def get_prefix(client, message):
    if not message.guild:
        return commands.when_mentioned_or(config.PREFIX)(client, message)
    guild_id = str(message.guild.id)
    if guild_id in client.prefixes:
        prefix = client.prefixes.get(guild_id, config.PREFIX)
    else:
        dbsearch = await client.mdb['prefixes'].find_one({'guild_id': guild_id})
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
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_URL)
        self.mdb = self.mongo_client[config.MONGO_DB]
        self.muted = set()
        self.prefixes = dict()
        self.api_keys = {
            'dbl_api_key': config.DBL_API_KEY,
            'server_api_url': config.API_URL,
            'server_api_key': config.API_KEY
        }
        self.personal_server = {
            'server_id': None,
            'sheet_channel': None,
            'general_channel': None
        }
        self.sentry_url = config.SENTRY_URL
        super(FrogBot, self).__init__(command_prefix, description=desc, **options)

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

    async def update_status_from_db(self):
        current_status = await self.mdb['bot_settings'].find_one({'setting': 'status'})
        if current_status is None:
            current_status = f'{config.DEFAULT_STATUS} | {config.PREFIX}help'
        else:
            current_status = f'{current_status["status"]} | {config.PREFIX}help'
        activity = discord.Game(name=current_status)
        return activity

    async def update_muted_from_db(self):
        muted = []
        db_muted = self.mdb.muted_clients.find()
        async for muted_user in db_muted:
            muted.append(muted_user['_id'])
        self.muted = muted
        return muted

    # ---- Overrides ----
    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)


intents = discord.Intents(
    guilds=True, members=True, messages=True, reactions=True,
    bans=False, emojis=True, integrations=False, webhooks=False, invites=False, voice_states=False, presences=True,
    typing=False
)

description = 'Small bot made for Play-by-Post Dungeons & Dragons.\n' \
              'Written by Dr Turtle#1771'

bot = FrogBot(desc=description, intents=intents,
              allowed_mentions=discord.AllowedMentions.none())

log_formatter = logging.Formatter('%(levelname)s | %(name)s: %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
log = logging.getLogger('bot')

# Make discord logs a bit quieter
logging.getLogger('discord.gateway').setLevel(logging.WARNING)
logging.getLogger('discord.client').setLevel(logging.WARNING)


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


@tasks.loop(seconds=5, count=1)
async def db_update():
    result = await bot.mdb['bot_settings'].find_one({'setting': 'personal_server'})
    if result is not None:
        for key in ['server_id', 'sheet_channel', 'general_channel']:
            bot.personal_server[key] = result.get(key, None)

    log.info('Updating Status and Muted from DB')
    new_status = await bot.update_status_from_db()
    await bot.change_presence(activity=new_status)
    await bot.update_muted_from_db()


@db_update.before_loop
async def before_db_update():
    await bot.wait_until_ready()


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if not bot.is_ready():
        return

    if message.author.id in bot.muted:
        return

    context = await bot.get_context(message)
    if context.command is not None:
        return await bot.invoke(context)
    else:
        if 'CustomCommands' in bot.cogs:
            await bot.cogs['CustomCommands'].run_custom_commands(context)


@bot.event
async def on_command(ctx):
    if ctx.command.name in ['py', 'pyi', 'sh']:
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

    if config.SENTRY_URL is not None:
        bot.sentry = sentry_sdk.init(config.SENTRY_URL, traces_sample_rate=1)

    db_update.start()
    bot.run(config.TOKEN)
