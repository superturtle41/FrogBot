import os
from datetime import datetime

import psutil
from discord.ext import commands

from utils.functions import create_default_embed


def time_to_readable(delta_uptime):
    hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    return f"{days}d, {hours}h, {minutes}m, {seconds}s"


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._command_count = None

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
        embed = create_default_embed(ctx)
        embed.title = 'FrogBot Uptime'
        bot_up = time_to_readable(self.bot.uptime)
        embed.add_field(name='Bot Uptime', value=f'{bot_up}')
        if ctx.bot.is_ready():
            embed.add_field(name='Ready Uptime',
                            value=f'{time_to_readable(datetime.utcnow() - self.bot.ready_time)}')
        return await ctx.send(embed=embed)

    @commands.command(name='info', aliases=['stats', 'about'])
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
            out = f'{ctx.author.display_name}: ' + repeat
        return await ctx.send(out)

    @commands.command(name='source')
    async def source(self, ctx):
        """
        Returns the link to the source code of the bot.
        """
        embed = create_default_embed(ctx)
        embed.title = 'FrogBot Source'
        embed.description = '[Click here for the Source Code.](https://github.com/1drturtle/FrogBot)'
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        await ctx.send(embed=embed)

    @commands.command(name='debug')
    async def debug(self, ctx):
        """
        Debugging commands for FrogBot
        """
        embed = create_default_embed(ctx)
        embed.title = 'FrogBot Debug'
        # -- Calculate Values --
        proc = psutil.Process(os.getpid())
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        mem_used = proc.memory_full_info().uss
        if self._command_count is None:
            self._command_count = len([command for cog in self.bot.cogs
                                       for command in self.bot.get_cog(cog).walk_commands()])
        command_count = self._command_count
        # -- Add fields ---
        embed.add_field(name='Memory Usage', value=f'{round((mem_used / 1000000), 2)} '
                                                   f'/ {round((mem.total / 1000000), 2)} MB '
                                                   f'({round(100 * (mem_used / mem.total), 2)}%)')
        embed.add_field(name='CPU Usage', value=f'{round(cpu, 2)}%')
        embed.add_field(name='Commands', value=f'{command_count} total commands loaded.')

        await ctx.send(embed=embed)

    @commands.command(name='invite')
    async def send_invite(self, ctx):
        """
        Sends a link to invite FrogBot
        """
        embed = create_default_embed(ctx)
        embed.title = 'FrogBot Invite Link'
        embed.description = '[Click here to invite FrogBot to your server!]' \
                            '(https://discord.com/api/oauth2/authorize' \
                            '?client_id=717467616700006482' \
                            '&permissions=470117462' \
                            '&scope=bot)'
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))
