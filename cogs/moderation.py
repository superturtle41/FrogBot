import discord
from discord.ext import commands

from utils.checks import able_to_ban, is_owner
from utils.functions import create_default_embed
from utils.constants import ABLE_TO_BAN
from typing import Union


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ban')
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check_any(commands.has_permissions(ban_members=True), able_to_ban(ABLE_TO_BAN))
    async def ban_member(self, ctx, who_to_ban: Union[discord.Member, discord.User], *, reason: str = None):
        """
        Bans a user from the server.

        You must either have the Ban Members permission, or have a role called Bot Admin.
        The bot must also have permission to ban the member and be above the member
        """
        if isinstance(who_to_ban, discord.Member) and ctx.guild.me.top_role < who_to_ban.top_role:
            return await ctx.send(f'I cannot ban {who_to_ban.mention}, as they have a higher role than me.')
        reason = 'No reason provided.' if reason is None else reason
        reason = f'Banned by {ctx.author.name}#{ctx.author.discriminator}: {reason}'
        await ctx.guild.ban(discord.Object(id=who_to_ban.id), reason=reason)
        return await ctx.send(f'{who_to_ban.mention} has been banned for the server with reason: {reason}')

    @commands.command(name='unban')
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check_any(commands.has_permissions(ban_members=True), able_to_ban(ABLE_TO_BAN))
    async def unban_member(self, ctx, who_to_ban: Union[discord.Member, discord.User], *, reason: str = None):
        """
        Un-bans a user from the server.

        You must either have the Ban Members permission, or have a role called Bot Admin.
        """
        reason = 'No reason provided.' if reason is None else reason
        reason += f'\nUn-banned by {ctx.author.name}#{ctx.author.discriminator}: '
        try:
            await ctx.guild.unban(discord.Object(id=who_to_ban.id), reason=reason)
        except discord.HTTPException:
            return await ctx.send(f'I was unable to un-ban {who_to_ban.mention}')
        return await ctx.send(f'{who_to_ban.mention} has been un-banned for the server with reason: {reason}')


def setup(bot):
    bot.add_cog(Moderation(bot))
