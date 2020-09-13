import logging

import discord
import utils.checks as checks
from discord.ext import commands
from utils.functions import get_positivity
from utils.objects import DMCategory
import logging

log = logging.getLogger('channels')


class QuestChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.mdb['quest-channels']
        self.messages = {'no_cat': "DM Category not found."}

    @commands.group(name='dm', description='Base command for all other DM Channel commands.'
                                           ' All subcommands require DM role.')
    @checks.is_dm()
    async def dm_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid Sub-command passed')

    @dm_group.command(name='setup', description='Sets up a DM Category.')
    async def dm_setup(self, ctx):
        cat = await DMCategory.create(self, ctx)
        if cat == -1:
            return await ctx.send('DM Category is already setup.')
        else:
            return await ctx.send('DM Category created.')

    @dm_group.command(name='delete', description='Deletes a DM category. Requires DM role.')
    async def dm_delete(self, ctx):
        category = DMCategory.from_ctx(self, ctx)
        await category.delete(ctx)

    @dm_group.command(name='allow', description='Allow a member to your DM channel.')
    async def dm_hub_allow(self, ctx, mem: discord.Member = None):
        """Allow a user into a DM hub by adding their perms."""
        cat = DMCategory.from_ctx(self, ctx)
        if cat is None:
            return await ctx.send(self.messages['no_cat'])
        result = await cat.allow(mem.id)
        if result == -1:
            return await ctx.send(f'User already in allowed list.')
        await ctx.send(f'Added {mem.display_name} to your DM Hub.')

    @dm_group.command(name='deny', description='Remove a member from your DM channel.')
    async def dm_hub_deny(self, ctx, mem: discord.Member = None):
        """Deny a user from a DM hub by removing their perms."""
        cat = DMCategory.from_ctx(self, ctx)
        if cat is None:
            return await ctx.send(self.messages['no_cat'])
        result = await cat.deny(mem.id)
        if result == -1:
            return await ctx.send(f'User not in allowed list.')
        await ctx.send(f'Removed {mem.display_name} to your DM Hub.')

    @dm_group.command(name='list', description='List allowed people in your channel.')
    async def dm_hub_list(self, ctx):
        cat = DMCategory.from_ctx(self, ctx)
        if cat is None:
            return await ctx.send(self.messages['no_cat'])
        message = 'Allowed Members in your hub channel:\n'
        for member_id in cat.allowed:
            member = self.bot.get_user(member_id)
            if member is not None:
                message += f'<:white_medium_small_square:746529103233941514> {member.display_name}\n'
        await ctx.send(message)

    @dm_group.command(name='addrole', description='Adds a quest role to all current channels.', aliases=['ar'])
    async def dm_all_allowrole(self, ctx, role: discord.Role):
        """Allow a role into RP channels by adding perms."""
        cat = DMCategory.from_ctx(self, ctx)
        if cat is None:
            return await ctx.send(self.messages['no_cat'])
        result = await cat.add_role(role)
        if result == -1:
            return await ctx.send(f'Role already in allowed list.')
        await ctx.send(f'Added {role.name} to your RP channels.')

    @dm_all_allowrole.error
    async def dm_all_allowrole_nf(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Role not found.')

    @dm_group.command(name='removerole', description='Removes a quest role to all current channels.', aliases=['rr'])
    async def dm_all_removerole(self, ctx, role: discord.Role):
        """Remove a role from RP channels by removing perms."""
        cat = DMCategory.from_ctx(self, ctx)
        if cat is None:
            return await ctx.send(self.messages['no_cat'])
        result = await cat.remove_role(role)
        if result == -1:
            return await ctx.send(f'Role not in allowed list.')
        await ctx.send(f'Removed {role.name} from your RP channels.')

    @dm_all_removerole.error
    async def dm_all_removerole_nf(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Role not found.')

    @dm_group.command(name='updaterole', description='Updates all your channels with current roles.', aliases=['uc'])
    async def dm_all_update(self, ctx):
        """Remove a role from RP channels by removing perms."""
        cat = DMCategory.from_ctx(self, ctx)
        if cat is None:
            return await ctx.send(self.messages['no_cat'])
        await cat.update_channels()
        await ctx.send(f'Updated roles for your RP channels (not your hub).')

    @dm_group.command(name='listroles', description='List current roles allowed in RP channels.', aliases=['lr'])
    async def dm_all_listroles(self, ctx):
        cat = DMCategory.from_ctx(self, ctx)
        if cat is None:
            return await ctx.send(self.messages['no_cat'])
        message = 'Allowed Roles in your RP channels:\n'
        for role_id in cat.roles:
            role = ctx.guild.get_role(role_id)
            if role is not None:
                message += f'<:white_medium_small_square:746529103233941514> {role.name}\n'
        await ctx.send(message)

    @dm_group.command(name='archive', description='Archives a RP channel.', aliases=['a'])
    async def dm_rp_archive(self, ctx, channel: discord.TextChannel):
        """Archives a channel"""
        cat = DMCategory.from_ctx(self, ctx)
        if cat is None:
            return await ctx.send(self.messages['no_cat'])
        result = await cat.archive(channel)
        if result == -1:
            return await ctx.send(f'Channel already in archived list.')
        await ctx.send(f'Added {channel.name} to your archived channels.')

    @dm_group.command(name='unarchive', description='Unarchives a RP channel', aliases=['ua'])
    async def dm_rp_unarchive(self, ctx, channel: discord.TextChannel):
        """Unarchives a channel"""
        cat = DMCategory.from_ctx(self, ctx)
        if cat is None:
            return await ctx.send(self.messages['no_cat'])
        result = await cat.archive(channel)
        if result == -1:
            return await ctx.send(f'Channel not in archived list.')
        await ctx.send(f'Removed {channel.name} from your archived channels.')

    @dm_group.command(name='listarchived', description='List Archived Channels', aliases=['la'])
    async def dm_rp_archivelist(self, ctx):
        cat = DMCategory.from_ctx(self, ctx)
        if cat is None:
            return await ctx.send(self.messages['no_cat'])
        message = 'Archived Channels:\n'
        if len(cat.archived) == 0:
            return await ctx.send('No channels currently archived.')
        for channel_id in cat.archived:
            channel = self.bot.get_user(channel_id)
            if channel is not None:
                message += f'<:white_medium_small_square:746529103233941514> {channel.name}\n'
        await ctx.send(message)


def setup(bot):
    bot.add_cog(QuestChannels(bot))
