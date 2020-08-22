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
