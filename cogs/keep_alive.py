from discord.ext import commands, tasks
import aiohttp
import logging

log = logging.getLogger(__name__)


class KeepAlive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        if (url := self.bot.config.API_URL) and (key := self.bot.config.API_KEY):
            self.url = url
            self.key = key
            self.alive_post.start()

    def cog_unload(self):
        self.alive_post.cancel()

    @tasks.loop(seconds=300)
    async def alive_post(self):
        headers = {'x-api-key': self.key}
        try:
            async with self.session.post(url=self.url, headers=headers) as _:
                pass
                # log.info(f'Uptime Post Response: {r.status}\n{await r.text()}')
        except aiohttp.client_exceptions.ClientConnectorError:
            log.error('Could not connect to API!')

    @alive_post.before_loop
    async def before_alive(self):
        await self.bot.wait_until_ready()
        log.info('Starting Uptime Loop')


def setup(bot):
    bot.add_cog(KeepAlive(bot))
