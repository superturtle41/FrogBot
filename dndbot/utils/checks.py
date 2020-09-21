from discord.ext import commands
from utils import constants
import discord


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == constants.DEV_ID

    return commands.check(predicate)


class NotAuthorized(commands.CheckFailure):
    pass


def is_dm():
    async def predicate(ctx):
        if len([role for role in ctx.author.roles if role.name.lower() == 'dm']) >= 1:
            return True
        else:
            raise NotAuthorized('Not DM')

    return commands.check(predicate)


def is_guild_owner():
    def predicate(ctx):
        return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id
    return commands.check(predicate)
