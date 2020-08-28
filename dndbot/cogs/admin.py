from discord.ext import commands
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


def setup(bot):
    bot.add_cog(Admin(bot))
