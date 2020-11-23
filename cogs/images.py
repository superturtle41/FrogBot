from discord.ext import commands
import aiohttp
from utils.functions import create_default_embed


def remove_queries_from_url(url: str) -> str:
    return url[:url.find('?')]


def url_from_context(ctx, url: str = None) -> str:
    if url is None:
        if len(ctx.message.attachments):
            url = ctx.message.attachments[0].url
        if url == '404' or url is None:
            url = str(ctx.author.avatar_url_as(format='jpeg'))
    return url


class Images(commands.Cog):
    """
    Commands made using various image API's
    """
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self._cd = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.user)


def setup(bot):
    bot.add_cog(Images(bot))
