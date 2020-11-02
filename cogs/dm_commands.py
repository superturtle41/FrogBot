import asyncio

import discord
from discord.ext import commands
import typing

from utils.checks import is_owner
from utils.functions import create_default_embed, get_positivity, try_delete
from .models.dm_objects import DMCategory, CategoryExists, DMPermissions, DMChannel


async def get_category_and_embed(ctx):
    current_cat: DMCategory = await DMCategory.from_ctx(ctx)
    embed = create_default_embed(ctx)
    if current_cat is None:
        embed.title = f'{ctx.author.display_name} does not have a DM Category!'
        embed.description = f'Create a DM Category with `{ctx.prefix}dm setup`'
    return current_cat, embed, (current_cat is not None)


class DMCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='dm', invoke_without_command=True)
    @commands.check_any(commands.has_role('DM'), is_owner())
    async def dm(self, ctx):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            embed.title = f'{ctx.author.display_name} checks their DM Category!'
            embed.description = f'Number of Channels: {len(current_cat.channels)}'
            for channel in current_cat.channels:
                embed.add_field(name=channel.channel.name,
                                value=channel.channel.topic if channel.channel.topic else 'No Topic', inline=True)
            embed.set_footer(text=f'{embed.footer.text} '
                                  f'| Not what you expected? Double check you entered a valid subcommand.')
        return await ctx.send(embed=embed)

    @dm.command(name='setup', description='Creates a DM Category.', aliases=['create', 'new'])
    async def dm_setup(self, ctx):
        try:
            new_category = await DMCategory.new(self.bot, ctx.guild, ctx.author)
        except CategoryExists:
            return await ctx.send(f'You already have a DM Category in this server. If this is an error, '
                                  f'run `{ctx.prefix}dm delete` and then run this command again.')
        embed = create_default_embed(ctx)
        embed.title = f'{ctx.author.display_name} creates their DM Category!'
        embed.description = f'Your DM Category has been created.\nThe default channel is ' \
                            f'<#{new_category.channels[0].channel.id}>'
        return await ctx.send(embed=embed)

    @dm.command(name='delete', description='Deletes a DM Category.', aliases=['remove', 'del'])
    async def dm_delete(self, ctx):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            confirm = await ctx.send('You are trying to delete your DM Category. Please Confirm (Yes/No)')

            def check(m):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            try:
                response = await self.bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send('Timed out waiting for answer.')
                return
            if not get_positivity(response.content):
                await ctx.send('Category deletion cancelled.')
                return
            embed.title = f'{ctx.author.display_name} deletes their DM Category!'
            embed.description = f'Deleting {len(current_cat.channels)} channels.'

            await try_delete(confirm)
            await try_delete(response)

            await current_cat.delete(self.bot)
        await ctx.send(embed=embed)

    @dm.command(name='update', description='Syncs all Channel Permissions', aliases=['uc'])
    async def dm_update(self, ctx):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            new_channels = len(await current_cat.sync_permissions(self.bot))
            embed.title = f'{ctx.author.display_name} updates their DM Channels.'
            embed.description = f'Updated {new_channels} new channel(s) and synced all permissions.'
        await ctx.send(embed=embed)

    # Roles

    @dm.command(name='addrole', description='Adds a role to a channel with read/write.')
    async def dm_add_role(self, ctx, channel_to_change: discord.TextChannel, to_add: discord.Role, type_: int = 1):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == channel_to_change.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            channel: DMChannel = channel[0]
            new_perms = DMPermissions(type_=0, perm_type=type_, obj=to_add, guild=ctx.guild)
            await channel.add_permission(new_perms)
            current_cat.commit(self.bot)
            embed.title = f'{ctx.author.display_name} adds {to_add.name} to #{channel.channel.name}'
            embed.description = f'{to_add.name} has been added to #{channel.channel.name}' \
                                f' with {new_perms.perm_type} permissions'
        return await ctx.send(embed=embed)

    @dm.command(name='addrole-all', description='Adds a role to all of your DM channels.')
    async def dm_add_role_all(self, ctx, to_add: discord.Role, type_: typing.Optional[int] = 1,
                              ignore: discord.TextChannel = None):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            embed.title = f'{ctx.author.display_name} adds {to_add.name} to all DM channels.'
            for channel in current_cat.channels:
                if ignore is not None:
                    if channel.channel.id == ignore.id:
                        embed.add_field(name=channel.channel.name, value='Ignored.')
                        continue
                new_perms = DMPermissions(type_=0, perm_type=type_, obj=to_add, guild=ctx.guild)
                await channel.add_permission(new_perms)
                current_cat.commit(self.bot)
                embed.add_field(name=channel.channel.name, value=f'Added @{to_add.name} with {new_perms.perm_type}')
        return await ctx.send(embed=embed)

    @dm.command(name='removerole', description='Removes a role from a channel.')
    async def dm_remove_role(self, ctx, channel_to_change: discord.TextChannel, to_remove: discord.Role):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == channel_to_change.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            channel: DMChannel = channel[0]
            result = await channel.remove_perm_for(to_remove)
            current_cat.commit(self.bot)
            if result:
                embed.title = f'{ctx.author.display_name} removes {to_remove.name} from {channel_to_change.name}!'
                embed.description = f'{to_remove.name} has been removed from {channel_to_change.name}.'
            else:
                embed.title = f'{ctx.author.display_name} tries to remove {to_remove.name} from {channel_to_change.name}!'
                embed.description = f'There is no existing permission for {to_remove.name} in {channel_to_change.name}.'
            await channel.sync_permissions()
        return await ctx.send(embed=embed)

    @dm.command(name='removerole-all', description='Removes a roll from all channels.')
    async def dm_remove_role_all(self, ctx, to_remove: discord.Role):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            embed.title = f'{ctx.author.display_name} removes {to_remove.name} from all DM channels!'
            for channel in current_cat.channels:
                result = await channel.remove_perm_for(to_remove)
                if result:
                    embed.add_field(name=channel.channel.name, value=f'Removed Permissions for {to_remove.name}')
            current_cat.commit(self.bot)
            await channel.sync_permissions()
        return await ctx.send(embed=embed)

    # Users

    @dm.command(name='adduser', description='Adds a user to a channel with read/write')
    async def dm_add_user(self, ctx, channel_to_change: discord.TextChannel, to_add: discord.Member, type_: int = 1):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == channel_to_change.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            channel: DMChannel = channel[0]
            new_perms = DMPermissions(type_=1, perm_type=type_, obj=to_add, guild=ctx.guild)
            await channel.add_permission(new_perms)
            current_cat.commit(self.bot)
            embed.title = f'{ctx.author.display_name} adds {to_add.display_name} to #{channel.channel.name}'
            embed.description = f'{to_add.display_name} has been added to ' \
                                f'#{channel.channel.name} with {new_perms.perm_type} permissions'
        return await ctx.send(embed=embed)

    @dm.command(name='removeuser', description='Removes a user from a channel')
    async def dm_remove_user(self, ctx, channel_to_change: discord.TextChannel, to_remove: discord.Member):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == channel_to_change.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            channel: DMChannel = channel[0]
            result = await channel.remove_perm_for(to_remove)
            current_cat.commit(self.bot)
            if result:
                embed.title = f'{ctx.author.display_name} removes ' \
                              f'{to_remove.display_name} from #{channel_to_change.name}!'
                embed.description = f'{to_remove.display_name} has been removed from #{channel_to_change.name}.'
            else:
                embed.title = f'{ctx.author.display_name} tries to remove ' \
                              f'{to_remove.display_name} from #{channel_to_change.name}!'
                embed.description = f'There is no existing permission for ' \
                                    f'{to_remove.display_name} in #{channel_to_change.name}.'
            await channel.sync_permissions()
        return await ctx.send(embed=embed)

    # Util Commands

    @dm.command(name='list', description='List permissions for a certain channel.')
    async def dm_list_perms(self, ctx, channel: discord.TextChannel = None):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            if channel is None:
                channel = ctx.channel
            channel = next((dmc for dmc in current_cat.channels if dmc.channel.id == channel.id), None)
            if channel is None:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            embed.title = f'List of special permissions for {channel.channel.name}'
            for permission in channel.permissions:
                embed.add_field(name=f'{permission.object_type}: {permission.applies_to.name}',
                                value=permission.perm_type)
        await ctx.send(embed=embed)

    @dm.command(name='port_old_channels', hidden=True)
    @is_owner()
    async def dm_port_old(self, ctx, old_category: discord.CategoryChannel, hub_channel: discord.TextChannel,
                          owner: discord.Member):
        category: DMCategory = await DMCategory.new_from_old(self.bot, ctx.guild, owner, old_category, hub_channel)
        return await ctx.send(str(category))


def setup(bot):
    bot.add_cog(DMCommands(bot))
