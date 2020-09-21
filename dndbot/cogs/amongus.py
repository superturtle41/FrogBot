from discord.ext import commands
import discord
from utils.checks import is_owner, is_guild_owner


def get_vc_from_user(author):
    return author.voice.channel


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muted_channels = []
        self.dead = {}

    async def channel_mute_toggle(self, vc, mute=True):
        if vc is None:
            return None
        for member in vc.members:
            if member.id in self.dead:
                continue
            await member.edit(mute=mute)

    @commands.command(name='amongus', description='Toggles muted/unmuted channel', aliases=['atm'])
    @commands.check_any(is_owner(), is_guild_owner(), commands.guild_only())
    async def amongus(self, ctx):
        vc = get_vc_from_user(ctx.author)
        if vc is None:
            return await ctx.send('Error: Not in voice channel.')
        if vc.id in self.muted:
            self.muted.remove(vc.id)
            self.channel_mute_toggle(vc)
        else:
            self.muted.append(vc.id)
            self.channel_mute_toggle(mute=False)

    @amongus.error
    async def amongus_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send('Invalid permissions, must be server owner or bot owner.')

    @commands.command(name='dead', description='Toggles user to dead (muted).', aliases=['ad'])
    @commands.guild_only()
    async def amongus_dead(self, ctx, member: discord.Member = None):
        user = ctx.author
        if member is not None:
            user = member
        vc = get_vc_from_user(user)
        if vc is None:
            return await ctx.send('Error: Not in voice channel.')
        if str(ctx.vc.id) not in self.dead:
            self.dead[str(ctx.vc.id)] = []
        if ctx.author.id in self.dead[str(ctx.vc.id)]:
            self.dead[str(ctx.vc.id)].remove(user.id)
        else:
            self.dead[str(ctx.vc.id)].append(user.id)


def setup(bot):
    bot.add_cog(Utils(bot))
