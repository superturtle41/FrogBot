from discord.ext import commands
from utils.functions import create_default_embed
from utils.checks import is_owner, is_guild_owner


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muted = []

    @commands.command(name="uptime", description="Prints uptime of bot.", aliases=['up', 'info'])
    async def timeup(self, ctx):
        embed = create_default_embed(self.bot, ctx)
        embed.title = '<:clock:743943384648908850> Current Uptime <:clock:743943384648908850>'
        embed.description = f'{str(self.bot.uptime).split(".", 2)[0]}'
        embed.add_field(name='Version', value=f'Current Version: {self.bot.version}')
        await ctx.send(embed=embed)

    @commands.command(name="say", description="Repeats what you said.", aliases=['echo'])
    async def repeat(self, ctx, message: str = ''):
        if message == '':
            return await ctx.send('Empty Message.')
        if ctx.author.id == self.bot.owner:
            return await ctx.send(message)
        else:
            return await ctx.send(f'{ctx.author.display_name}: **{message}**')

    @commands.command(name='amongus', description='Toggles muted/unmuted channel', aliases=['atm'])
    @commands.check_any(is_owner(), is_guild_owner())
    async def amongus(self, ctx):
        vc = ctx.message.author.voice.channel
        if vc is None:
            return ctx.send('Not in voice channel.')
        if vc.id in self.muted:
            for member in vc.members:
                await member.edit(mute=False)
            self.muted.remove(vc.id)
        else:
            self.muted.append(vc.id)
            for member in vc.members:
                await member.edit(mute=True)


def setup(bot):
    bot.add_cog(Utils(bot))
