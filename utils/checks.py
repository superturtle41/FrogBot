from discord.ext import commands
import bot_config as config
from utils.errors import UnauthorizedServer, IsNotDM
from utils.constants import ABLE_TO_BAN


def _is_owner_check(author_id):
    return author_id == config.DEV_ID


def is_owner():
    async def predicate(ctx):
        return _is_owner_check(ctx.author.id)

    return commands.check(predicate)


def is_personal_server():
    async def predicate(ctx):
        if ctx.bot.personal_server['server_id'] is None:
            raise UnauthorizedServer('This command is not allowed to be run in this server.')
        return ctx.guild_id == ctx.bot.personal_server['server_id']

    return commands.check(predicate)


def can_use_dm():
    async def predicate(ctx):
        # does the bot have permissions?
        if ctx.guild_id is None:
            raise commands.NoPrivateMessage('This command cannot be used in DMs.'
                                            '')
        perms = ctx.me.guild_permissions
        if not perms.manage_channels:
            raise commands.BotMissingPermissions('manage_channels')
        if not perms.manage_messages:
            raise commands.BotMissingPermissions('manage_messages')
        # can the user use the command
        for role in ctx.author.roles:
            if role.name.lower() == 'dm':
                return True
        if _is_owner_check(ctx.author.id):
            return True
        raise IsNotDM('You must have a role called DM to perform this command.')
    return commands.check(predicate)


def able_to_ban():
    async def predicate(ctx):
        if len([r for r in ctx.author.roles if r.name.lower in ABLE_TO_BAN]):
            return True
        raise commands.BadArgument('You are not authorized to run this command!')
    return commands.check(predicate)
