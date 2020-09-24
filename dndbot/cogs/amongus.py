from discord.ext import commands
import discord
from utils.checks import is_owner, is_guild_owner


def get_vc_from_user(author):
    vc = author.voice
    if vc:
        return author.voice.channel
    return None


async def channel_mute_toggle(vc, mute=True):
    if vc is None:
        return None
    for member in vc.members:
        await member.edit(mute=mute)


class AmongUs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muted_channels = []

    @commands.command(name='amongus', description='Toggles muted/unmuted channel', aliases=['atm'])
    @commands.check_any(is_owner(), is_guild_owner(), commands.guild_only())
    async def amongus(self, ctx):
        vc = get_vc_from_user(ctx.author)
        if vc is None:
            return await ctx.send('Error: Not in voice channel.')
        mute_or_unmute = False
        if vc.id in self.muted_channels:
            self.muted_channels.remove(vc.id)
        else:
            self.muted_channels.append(vc.id)
            mute_or_unmute = True
        for member in vc.members:
            try:
                await member.edit(mute=mute_or_unmute)
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass

    @amongus.error
    async def amongus_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send('Invalid permissions, must be server owner or bot owner.')


def setup(bot):
    bot.add_cog(AmongUs(bot))
