from discord.ext import commands
from utils.checks import is_owner
from utils.functions import create_default_embed


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stop", description="Owner Only - Stops Bot", hidden=True)
    @is_owner()
    async def stop(self, ctx, really: str = "no"):
        await ctx.send("Okay, shutting down...")
        if really != "no":
            await ctx.send('<:eyes:746541266954617014>')
            await self.bot.logout()

    @stop.error
    async def stop_error(self, ctx, error):
        if isinstance(error, commands.errors.NotOwner) or isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have permission to stop the bot!")

    @commands.command(name="uptime", description="Prints uptime of bot.", aliases=['up', 'info'])
    async def timeup(self, ctx):
        embed = create_default_embed(self.bot, ctx)
        embed.title = '<:clock:743943384648908850> Current Uptime <:clock:743943384648908850>'
        embed.description = f'{str(self.bot.uptime).split(".", 2)[0]}'
        embed.add_field(name='Version', value=f'Current Version: {self.bot.version}')
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Admin(bot))
