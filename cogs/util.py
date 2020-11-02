from discord.ext import commands
from utils.checks import is_owner, is_authorized
import discord
from datetime import datetime


def time_to_readable(delta_uptime):
    hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    return f"{days}d, {hours}h, {minutes}m, {seconds}s"


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
        bot_up = time_to_readable(self.bot.uptime)
        if ctx.bot.is_ready():
            ready_up = time_to_readable(datetime.utcnow() - self.bot.ready_time)
        else:
            ready_up = None
        out = f'Current Bot Uptime: {bot_up}'
        if ready_up:
            out += '\n'+f'Current Ready Uptime{ready_up}'
        return await ctx.send(out)


def setup(bot):
    bot.add_cog(Utility(bot))
