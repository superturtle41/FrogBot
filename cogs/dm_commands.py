from discord.ext import commands
from .models.dm_objects import DMCategory
from utils.functions import create_default_embed
from utils.checks import is_owner


class DMCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='dm', invoke_without_command=True)
    @commands.check_any(commands.has_role('DM'), is_owner())
    async def dm(self, ctx):
        current_cat = await DMCategory.from_ctx(ctx)
        embed = create_default_embed(ctx)
        if current_cat is None:
            embed.title = f'{ctx.author.display_name} does not have a DM Category!'
            embed.description = f'Create a DM Category with {ctx.prefix}dm setup'
        else:
            embed.title = f'{ctx.author.display_name} checks their DM Category!'
            embed.description = f'Number of Channels: {len(current_cat.channels)}'
            for channel in current_cat:
                embed.add_field(value=channel.channel.name, inline=True)
        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(DMCommands(bot))
