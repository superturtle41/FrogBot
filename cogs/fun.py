from discord.ext import commands
from random import randint
from utils.functions import create_default_embed


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='choice', aliases=['choose'])
    async def choice(self, ctx, *, choices: str):
        """
        Makes a choice for you.
        """
        embed = create_default_embed(ctx)
        embed.title = 'Choices!'
        choices = choices.split(' ')
        choice = randint(0, len(choices) - 1)

        embed.add_field(name='Possible Choices', value=', '.join(choices))
        embed.add_field(name='Rolled', value=f'Rolled 1d{len(choices)}: `{choice+1}`')
        embed.description = choices[choice]
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
