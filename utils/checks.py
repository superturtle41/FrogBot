from discord.ext import commands
import bot_config as config


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == config.DEV_ID

    return commands.check(predicate)


def is_authorized():
    async def predicate(ctx):
        authorized = await ctx.bot.mdb['authorized'].find_one({'_id': ctx.author.id})
        return authorized is not None

    return commands.check(predicate)


def is_personal_server():
    async def predicate(ctx):
        if ctx.bot.personal_server is None:
            return False
        return ctx.guild_id == ctx.bot.personal_server

    return commands.check(predicate)
