from discord.ext import commands
import bot_config as config


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == config.DEV_ID

    return commands.check(predicate)

