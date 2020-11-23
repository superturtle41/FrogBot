import discord
from discord.ext import commands

from utils.checks import able_to_ban, is_owner
from utils.functions import create_default_embed


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ban')
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check_any(commands.has_permissions(ban_members=True), is_owner(), able_to_ban())
    async def ban_member(self, ctx, who_to_ban: discord.Member, *, reason: str = None):
        """
        Bans a user from the server.

        You must either have the Ban Members permission, or have a role called Bot Admin.
        The bot must also have permission to ban the member and be above the member
        """
        if ctx.guild.me.top_role < who_to_ban.top_role:
            return await ctx.send(f'I cannot ban {who_to_ban.mention}, as they have a higher role than me.')
        reason = 'No reason provided.' if reason is None else reason
        await ctx.guild.ban(who_to_ban, reason)
        return await ctx.send(f'{who_to_ban.mention} has been banned for the server with reason: {reason}')


def setup(bot):
    bot.add_cog(Moderation(bot))
