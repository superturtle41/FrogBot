from discord.ext import commands


class DMCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(DMCommands(bot))
