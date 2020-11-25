import collections
import re

import aiohttp
import discord
from discord.ext import commands
from utils.errors import APIError
import io

FakeCoolDown = collections.namedtuple('FakeCoolDown', ['rate', 'per', 'type'])


def remove_queries_from_url(url: str) -> str:
    """
    Returns all content before the first `?` in a string.
    """
    if r := url.find('?'):
        return url[:r]
    return url


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
        self.url_regex = re.compile(r'(http(s?):)([/|.|\w|\s|-])*\.(?:jpg|jpeg|gif|png)')

    async def cog_check(self, ctx):
        bucket = self._cd.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            if ctx.author.id == self.bot.owner:
                return True
            cooldown = FakeCoolDown(1, 30, commands.BucketType.user)
            raise commands.CommandOnCooldown(cooldown, bucket.get_retry_after())
        return True

    async def image_response(self, url) -> discord.File:
        """
        Takes a URL, makes a GET request and returns a file if one is returned, otherwise raises an error.
        """
        async with self.session.get(url=url) as r:
            if r.status != 200:
                try:
                    error_json = await r.json()
                    error = error_json['error']
                except (aiohttp.ClientResponseError, KeyError):
                    error = 'The API raised an unknown error.'
                raise APIError(error)
            try:
                image_bytes_raw = await r.read()
                image_bytes = io.BytesIO(image_bytes_raw)
            except aiohttp.ClientResponseError:
                raise APIError('The API raised an unknown error.')
            return discord.File(image_bytes, filename='inverted.png')

    async def api_image_filter(self, filter_name: str, url: str) -> discord.File:
        """
        Takes a filter and a url to parse into some-random-api
        """
        base_url = f'https://some-random-api.ml/canvas/{filter_name}?avatar={url}'
        return await self.image_response(base_url)

    @commands.command(name='invert')
    async def invert_image(self, ctx, *, url: str):
        """
        Inverts the colors for a given URL.
        """
        url = remove_queries_from_url(url)
        is_valid_url = self.url_regex.findall(url)
        if not is_valid_url:
            return await ctx.send('That is not a valid image URL.')
        try:
            to_send = await self.api_image_filter(filter_name='invert', url=url)
        except APIError as error:
            return await ctx.send(f'Error: {str(error)}')
        await ctx.send(file=to_send)

    @commands.command(name='wasted')
    async def wasted_overlay(self, ctx, *, url: str):
        """
        Overlays the image with "wasted" from GTA.
        """
        with ctx.channel.typing():
            url = remove_queries_from_url(url)
            is_valid_url = self.url_regex.findall(url)
            if not is_valid_url:
                await ctx.send('That is not a valid image URL.')
                return
            try:
                to_send = await self.api_image_filter(filter_name='wasted', url=url)
            except APIError as error:
                await ctx.send(f'Error: {str(error)}')
                return
            await ctx.send(file=to_send)


def setup(bot):
    bot.add_cog(Images(bot))
