from discord.ext import commands
from utils.functions import get_uptime, create_default_embed
from utils.checks import is_owner


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
        minutes = get_uptime(self.bot)
        embed = create_default_embed(self.bot, ctx)
        embed.title = "**Current Bot Uptime**"
        embed.description = f'Bot has been running for ' \
                            f'{int(minutes[0])} {"minutes" if minutes[0]>=2 or minutes[0]==0 else "minute"} ' \
                            f'{round(minutes[1])} seconds. '
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Admin(bot))
