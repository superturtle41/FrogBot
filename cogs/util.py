from discord.ext import commands
from utils.checks import is_owner, is_authorized
import discord
from datetime import datetime


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping', description='Get the ping of the bot.')
    async def ping(self, ctx):
        now = datetime.now()
        message = await ctx.send('Ping!')
        await message.edit(content=f'Pong!\nBot: {int(ctx.bot.latency*1000)} ms\n'
                                   f'Discord: {int((datetime.now() - now).total_seconds()*1000)} ms')

    @commands.command(name='uptime', description='Displays the uptime of the bot.', aliases=['up', 'info'])
    async def uptime(self, ctx):
        return await ctx.send(f'The bot has been alive for: {str(self.bot.uptime).split(".", 2)[0]}')


def setup(bot):
    bot.add_cog(Utility(bot))
