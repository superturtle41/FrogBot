from discord.ext import commands
import bot_config as config


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == config.DEV_ID

    return commands.check(predicate)


def is_personal_server():
    async def predicate(ctx):
        if ctx.bot.personal_server['server_id'] is None:
            return False
        return ctx.guild_id == ctx.bot.personal_server['server_id']

    return commands.check(predicate)
