import asyncio

import discord
from discord.ext import commands

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

    @dm.command(name='addrole', description='Adds a role to a channel with read/write.')
    async def dm_add_role(self, ctx, channel_to_change: discord.TextChannel, to_add: discord.Role, type: int = 1):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == channel_to_change.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            channel: DMChannel = channel[0]
            new_perms = DMPermissions(type_=0, perm_type=type, obj=to_add, guild=ctx.guild)
            await channel.add_permission(new_perms)
            current_cat.commit(self.bot)
            embed.title = f'{ctx.author.display_name} adds {to_add.name} to #{channel.channel.name}'
            type_ = ['Admin', 'Read/Send', 'Read-Only', 'Hidden'][type]
            embed.description = f'{to_add.name} has been added to #{channel.channel.name} with {type_} permissions'
        return await ctx.send(embed=embed)

    @dm.command(name='removerole', description='Removes a roll from a channel.')
    async def dm_remove_roll(self, ctx, channel_to_change: discord.TextChannel, to_add: discord.Role):
        current_cat, embed, test = await get_category_and_embed(ctx)
        if test:
            channel = [dmchannel for dmchannel in current_cat.channels if dmchannel.channel.id == channel_to_change.id]
            if not channel:
                return await ctx.send(f'Channel was not found in your category. Try running `{ctx.prefix}dm update`')
            channel: DMChannel = channel[0]
            result = await channel.remove_perm_for(to_add)
            current_cat.commit(self.bot)
            if result:
                embed.title = f'{ctx.author.display_name} removes {to_add.name} from {channel_to_change.name}!'
                embed.description = f'{to_add.name} has been removed from {channel_to_change.name}.'
            else:
                embed.title = f'{ctx.author.display_name} tries to remove {to_add.name} from {channel_to_change.name}!'
                embed.description = f'There is no existing permission for {to_add.name} in {channel_to_change.name}.'
            await channel.sync_permissions()
        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(DMCommands(bot))
