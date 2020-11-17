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
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dm(self, ctx):
        """
        Base command for all other DM commands

        All DM commands require a rolled called DM.
        The bot must have the "Manage Channels" and "Manage Messages" permissions.
        """
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
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_setup(self, ctx):
        """
        Creates a new DM Category.

        Will also create one channel for you, this is supposed to be your hub channel, but you can use it for whatever.
        """
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
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_delete(self, ctx):
        """
        Deletes your DM category for that server.

        If you do not have a DM category it will do nothing.
        """
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            confirm = await ctx.prompt('You are trying to delete your DM Category.')
            if confirm is None:
                return await ctx.send('Timed out waiting for response.')
            elif not confirm:
                return await ctx.send('Category deletion cancelled.')
            embed.title = f'{ctx.author.display_name} deletes their DM Category!'
            embed.description = f'Deleting {len(current_cat.channels)} channels.'

            await current_cat.delete(self.bot)
        await ctx.send(embed=embed)

    @dm.command(name='update', description='Syncs all Channel Permissions', aliases=['uc'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_update(self, ctx):
        """
        Goes through all of the channels in your category and syncs them.

        Will add new channels to the bot's database and will sync the permissions of all channels.
        """
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            new_channels = len(await current_cat.sync_permissions(self.bot))
            embed.title = f'{ctx.author.display_name} updates their DM Channels.'
            embed.description = f'Updated {new_channels} new channel(s) and synced all permissions.'
        await ctx.send(embed=embed)

    # Roles

    @dm.command(name='addrole', description='Adds a role to a channel with read/write.', aliases=['ar'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_add_role(self, ctx, channel_to_change: discord.TextChannel, to_add: discord.Role, type_: int = 1):
        """
        Adds a role to a DM Channel with permissions.

        The channel must be in your category.
        For type, you can specify 0, 1, or 2. 0 = Channel Admin, 1 = Read/Send, 2 = Read Only (Spectator)
        """
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == channel_to_change.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            channel: DMChannel = channel[0]
            new_perms = DMPermissions(type_=0, perm_type=type_, obj=to_add, guild=ctx.guild)
            await channel.add_permission(new_perms)
            await current_cat.commit(self.bot)
            embed.title = f'{ctx.author.display_name} adds {to_add.name} to #{channel.channel.name}'
            embed.description = f'{to_add.name} has been added to #{channel.channel.name}' \
                                f' with {new_perms.perm_type} permissions'
        return await ctx.send(embed=embed)

    @dm.command(name='addrole-all', description='Adds a role to all of your DM channels.', aliases=['ara'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_add_role_all(self, ctx, to_add: discord.Role, type_: typing.Optional[int] = 1,
                              ignore: discord.TextChannel = None):
        """
        Adds a role to all of your DM Channels with permissions

        For type, you can specify 0, 1, or 2. 0 = Channel Admin, 1 = Read/Send, 2 = Read Only
        `ignore` is one channel you can specify that the command will ignore, usually your "DM Hub"/Secret Channel.
        """
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
                await current_cat.commit(self.bot)
                embed.add_field(name=channel.channel.name, value=f'Added @{to_add.name} with {new_perms.perm_type}')
        return await ctx.send(embed=embed)

    @dm.command(name='removerole', description='Removes a role from a channel.', aliases=['rr'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_remove_role(self, ctx, channel_to_change: discord.TextChannel, to_remove: discord.Role):
        """
        Removes a role from a DM Channel.
        """
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == channel_to_change.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            channel: DMChannel = channel[0]
            result = await channel.remove_perm_for(to_remove)
            await current_cat.commit(self.bot)
            if result:
                embed.title = f'{ctx.author.display_name} removes {to_remove.name} from {channel_to_change.name}!'
                embed.description = f'{to_remove.name} has been removed from {channel_to_change.name}.'
            else:
                embed.title = f'{ctx.author.display_name} tries to remove {to_remove.name} from {channel_to_change.name}!'
                embed.description = f'There is no existing permission for {to_remove.name} in {channel_to_change.name}.'
            await channel.sync_permissions()
        return await ctx.send(embed=embed)

    @dm.command(name='removerole-all', description='Removes a roll from all channels.', aliases=['rra'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_remove_role_all(self, ctx, to_remove: discord.Role):
        """
        Removes a role from all of your DM channels.
        """
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            embed.title = f'{ctx.author.display_name} removes {to_remove.name} from all DM channels!'
            for channel in current_cat.channels:
                result = await channel.remove_perm_for(to_remove)
                if result:
                    embed.add_field(name=channel.channel.name, value=f'Removed Permissions for {to_remove.name}')
            await current_cat.commit(self.bot)
            await channel.sync_permissions()
        return await ctx.send(embed=embed)

    # Users

    @dm.command(name='adduser', description='Adds a user to a channel with read/write', aliases=['au'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_add_user(self, ctx, channel_to_change: discord.TextChannel, to_add: discord.Member, type_: int = 1):
        """
        Adds a user to one of your DM Channels.

        For type, you can specify 0, 1, or 2. 0 = Channel Admin, 1 = Read/Send, 2 = Read Only
        """
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == channel_to_change.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            channel: DMChannel = channel[0]
            new_perms = DMPermissions(type_=1, perm_type=type_, obj=to_add, guild=ctx.guild)
            await channel.add_permission(new_perms)
            await current_cat.commit(self.bot)
            embed.title = f'{ctx.author.display_name} adds {to_add.display_name} to #{channel.channel.name}'
            embed.description = f'{to_add.display_name} has been added to ' \
                                f'#{channel.channel.name} with {new_perms.perm_type} permissions'
        return await ctx.send(embed=embed)

    @dm.command(name='removeuser', description='Removes a user from a channel', aliases=['ru'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_remove_user(self, ctx, channel_to_change: discord.TextChannel, to_remove: discord.Member):
        """
        Removes a user from one of your DM channels.
        """
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == channel_to_change.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            channel: DMChannel = channel[0]
            result = await channel.remove_perm_for(to_remove)
            await current_cat.commit(self.bot)
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

    # Channel Modification (Create/Delete)

    @dm.command(name='createchannel', aliases=['cc'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_create_channel(self, ctx, channel_name: str):
        """
        Creates a channel in your DM category.

        Cannot have two channels with the same name.
        """
        channel_name = channel_name.replace(' ', '-')
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = next((dmc for dmc in current_cat.channels if dmc.channel.name == channel_name), None)
            if channel is not None:
                return await ctx.send(f'There is already a channel named {channel_name} in your DM Category')
            await current_cat.category.create_text_channel(name=channel_name)
            await current_cat.sync_permissions(self.bot)
            embed.title = f'{ctx.author.display_name} creates a new channel!'
            embed.description = f'Channel with name {channel_name} has been created.'
        await ctx.send(embed=embed)

    @dm.command(name='deletechannel', aliases=['dc'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_delete_channel(self, ctx, channel_to_delete: discord.TextChannel):
        """
        Deletes a channel from your DM Category.

        Channel must be in your DM Category.
        """
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = next((dmc for dmc in current_cat.channels if dmc.channel.id == channel_to_delete.id), None)
            if channel is None:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            embed.title = f'{ctx.author.display_name} deletes {channel_to_delete.name}'
            embed.description = f'{channel_to_delete.name} has been deleted.'
            # Delete Channel
            current_cat.channels.pop(current_cat.channels.index(channel))
            await current_cat.commit(self.bot)
            try:
                await channel_to_delete.delete()
            except discord.HTTPException:
                pass
            await ctx.send(embed=embed)

    # Archive Commands
    @dm.command(name='archive', aliases=['arc'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_archive(self, ctx, channels: commands.Greedy[discord.TextChannel], archive=True):
        """
        Archives channels in your DM category.

        Will archive as many channels as are passed.
        """
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            for raw_channel in channels:
                channel = next((dmc for dmc in current_cat.channels if dmc.channel.id == raw_channel.id), None)
                index = current_cat.channels.index(channel)
                if channel is None:
                    return await ctx.send(
                        f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
                new_permissions = []
                for perm in channel.permissions:
                    if archive:
                        x = perm.change_type(2)
                        embed.add_field(name=raw_channel.name, value='Archived')
                    else:
                        x = perm.change_type(1)
                        embed.add_field(name=raw_channel.name, value='Unarchived')
                    new_permissions.append(x)
                channel.permissions = new_permissions
                current_cat.channels[index] = channel
            embed.title = f'{ctx.author.display_name} {"archives" if archive else "unarchives"} some channels!'
            await current_cat.sync_permissions(self.bot)
            await ctx.send(embed=embed)

    @dm.command(name='unarchive', aliases=['uarc'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_unarchive(self, ctx, channels: commands.Greedy[discord.TextChannel]):
        await ctx.invoke(self.dm_archive, channels=channels, archive=False)

    # Util Commands

    @dm.command(name='list', description='List permissions for a certain channel.')
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_list_perms(self, ctx, channel: discord.TextChannel = None):
        """
        List the permissions for a DM Channel.

        If no channel is specified, it will try to use the current channel.
        """
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

    @dm.command(name='resetchannel', description='Resets a channel to default permissions.', aliases=['rc'])
    @commands.check_any(commands.has_role('DM'), is_owner())
    @commands.bot_has_guild_permissions(manage_channels=True, manage_messages=True)
    async def dm_channel_reset(self, ctx, to_reset: discord.TextChannel):
        """
        Resets one of your DM Channels to default permissions.

        This just syncs the channel with the category.
        """
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == to_reset.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            await to_reset.edit(sync_permissions=True)
            channel = channel[0]
            channel.permissions = []
            await current_cat.commit(self.bot)
            embed.title = f'{ctx.author.display_name} resets the permissions of {to_reset.name}'
            embed.add_field(name=to_reset.name, value='Permissions Reset')
        await ctx.send(embed=embed)

    @dm.command(name='port_old_channels', hidden=True, aliases=['poc'])
    @is_owner()
    async def dm_port_old(self, ctx, old_category: discord.CategoryChannel, hub_channel: discord.TextChannel,
                          owner: discord.Member):
        category: DMCategory = await DMCategory.new_from_old(self.bot, ctx.guild, owner, old_category, hub_channel)
        return await ctx.send(str(category))


def setup(bot):
    bot.add_cog(DMCommands(bot))
