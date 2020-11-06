from discord.ext import commands
from utils.checks import is_owner, is_authorized
import discord
from utils.functions import create_default_embed
from datetime import datetime


def time_to_readable(delta_uptime):
    hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    return f"{days}d, {hours}h, {minutes}m, {seconds}s"


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx):
        """
        Gets the ping of the bot.
        """
        now = datetime.now()
        message = await ctx.send('Ping!')
        await message.edit(content=f'Pong!\nBot: {int(ctx.bot.latency*1000)} ms\n'
                                   f'Discord: {int((datetime.now() - now).total_seconds()*1000)} ms')

    @commands.command(name='uptime', aliases=['up', 'alive'])
    async def uptime(self, ctx):
        """
        Displays the current uptime of the bot.
        """
        bot_up = time_to_readable(self.bot.uptime)
        if ctx.bot.is_ready():
            ready_up = time_to_readable(datetime.utcnow() - self.bot.ready_time)
        else:
            ready_up = None
        out = f'Current Bot Uptime: {bot_up}'
        if ready_up:
            out += '\n'+f'Current Ready Uptime: {ready_up}'
        return await ctx.send(out)

    @commands.command(name='info', aliases=['stats'])
    async def info(self, ctx):
        """
        Displays some information about the bot.
        """
        embed = create_default_embed(ctx)
        embed.title = 'FrogBot Information'
        embed.description = 'Bot built by Dr Turtle#1771 made for D&D and personal servers!'
        members = sum([guild.member_count for guild in self.bot.guilds])
        embed.add_field(name='Guilds', value=f'{len(self.bot.guilds)}')
        embed.add_field(name='Members', value=f'{members}')
        embed.url = 'https://github.com/1drturtle/FrogBot'

        await ctx.send(embed=embed)

    @commands.command(name='say')
    async def say(self, ctx, *, repeat: str):
        """
        Repeats what you say.
        """
        out = repeat
        if ctx.author.id != self.bot.owner:
            out.prepend(f'{ctx.author.display_name}: ')
        return await ctx.send(out)


def setup(bot):
    bot.add_cog(Utility(bot))
