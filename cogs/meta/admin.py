from discord.ext import commands
from utils.checks import is_owner
import discord
from utils.functions import create_default_embed


def channel_id_to_link(channel_id):
    if isinstance(channel_id, discord.TextChannel):
        channel_id = channel_id.id
    return f'<#{channel_id}>'


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---- Bot Owner Commands ----
    @commands.group(name='admin', invoke_without_command=True)
    @is_owner()
    async def admin(self, ctx):
        """
        Owner only commands for the bot.
        """
        await ctx.send('give a subcommand nerd')

    @admin.command(name="restart")
    @is_owner()
    async def restart(self, ctx):
        """
        Stops the bot, restarting it.
        """
        confirm = await ctx.prompt('Are you sure you want to shutdown the bot?')
        if confirm:
            try:
                await self.bot.logout()
            except RuntimeError:
                pass

    @admin.command(name='change_status', description='Owner Only - Changes the bot\'s status.')
    @is_owner()
    async def change_status(self, ctx, *, value: str):
        """
        Changes the bot's status. Will reset if `reset` is passed.
        """
        if value != 'reset':
            await ctx.bot.mdb['bot_settings'].update_one({'setting': 'status'},
                                                         {'$set': {'status': value}}, upsert=True)
        else:
            await ctx.bot.mdb['bot_settings'].delete_one({'setting': 'status'})
        await ctx.bot.change_presence(activity=await ctx.bot.update_status_from_db())

        return await ctx.send(f'Status changed to {value}' if value != 'reset' else 'Status Reset.')

    @admin.group(name='personal_server', aliases=['ps'], invoke_without_command=True)
    @is_owner()
    async def personal_server(self, ctx):
        """
        Base command for personal server commands.

        Displays information about currently set personal server.
        """
        if self.bot.personal_server['server_id'] is None:
            return await ctx.send('Personal Server not set, no information available.')
        personal_server = self.bot.get_guild(self.bot.personal_server['server_id'])
        sheet_channel = channel_id_to_link(personal_server.get_channel(self.bot.personal_server['sheet_channel'])) \
            if self.bot.personal_server['sheet_channel'] is not None else 'Not set.'
        general_channel = channel_id_to_link(personal_server.get_channel(self.bot.personal_server['general_channel'])) \
            if self.bot.personal_server['general_channel'] is not None else 'Not set.'

        embed = create_default_embed(ctx)
        embed.title = 'FrogBot Personal Server Information'
        embed.add_field(name='Server Info', value=f'Server ID: {personal_server.id}\n'
                                                  f'Server Name: {personal_server.name}')
        embed.add_field(name='Channel Info', value=f'Sheet Channel: {sheet_channel}\n'
                                                   f'General Channel: {general_channel}')
        await ctx.send(embed=embed)

    @personal_server.command(name='set_server', aliases=['ss'])
    @is_owner()
    async def set_personal_server(self, ctx, guild_id: int):
        """
        Sets the bot's personal server. This is the server where SheetApproval works.
        """
        await ctx.bot.mdb['bot_settings'].update_one({'setting': 'personal_server'},
                                                     {'$set': {'server_id': guild_id}},
                                                     upsert=True
                                                     )
        self.bot.personal_server['server_id'] = guild_id

        return await ctx.send(f'Set {guild_id} to personal server.')

    @personal_server.command(name='set_sheet_channel', aliases=['ssc'])
    @is_owner()
    async def set_personal_sheet_channel(self, ctx, channel: discord.TextChannel):
        """
        Sets the sheet channel for the bot's personal server.
        """
        await ctx.bot.mdb['bot_settings'].update_one({'setting': 'personal_server'},
                                                     {'$set': {'sheet_channel': channel.id}},
                                                     upsert=True
                                                     )

        self.bot.personal_server['sheet_channel'] = channel.id

        return await ctx.send(f'Set <#{channel.id}> to sheet channel.')

    @personal_server.command(name='set_general_channel', aliases=['sgc'])
    @is_owner()
    async def set_personal_general_channel(self, ctx, channel: discord.TextChannel):
        """
        Sets the general channel for the bot's personal server.
        """
        await ctx.bot.mdb['bot_settings'].update_one({'setting': 'personal_server'},
                                                     {'$set': {'general_channel': channel.id}},
                                                     upsert=True
                                                     )

        self.bot.personal_server['general_channel'] = channel.id

        return await ctx.send(f'Set <#{channel.id}> to sheet channel.')

    @admin.command(name='leave')
    @is_owner()
    async def leave_guild(self, ctx, guild_id: int):
        """
        Leaves the specified guild
        """
        to_leave: discord.Guild = self.bot.get_guild(guild_id)
        if to_leave is not None:
            await ctx.send(f'Leaving Guild: `{to_leave.name}`')
            try:
                await to_leave.leave()
            except discord.HTTPException:
                pass
        else:
            return await ctx.send('Guild not found.')

    @admin.command(name='mute', description='Mutes a user. Prevents them from using the bot.')
    @is_owner()
    async def mute(self, ctx, to_mute: discord.Member):
        """
        Mutes a user from the bot.
        """
        record = {'_id': to_mute.id}
        db = self.bot.mdb['muted_clients']
        muted = await db.find_one(record)
        if muted is None:
            await db.insert_one(record)
            await self.bot.update_muted_from_db()
            return await ctx.send(f'User {to_mute.name}#{to_mute.discriminator} has been muted.')
        else:
            return await ctx.send(f'User {to_mute.name}#{to_mute.discriminator} has already been muted.')

    @admin.command(name='unmute', description='Un-mutes a user.')
    @is_owner()
    async def unmute(self, ctx, to_mute: discord.Member):
        """
        Unmutes a user from the bot.
        """
        record = {'_id': to_mute.id}
        db = self.bot.mdb['muted_clients']
        muted = await db.find_one(record)
        if muted:
            await db.delete_one(record)
            await self.bot.update_muted_from_db()
            return await ctx.send(f'User {to_mute.name}#{to_mute.discriminator} has been un-muted.')
        else:
            return await ctx.send(f'User {to_mute.name}#{to_mute.discriminator} is not muted.')

    # ---- Server Owner Commands ----

    @commands.command(name='prefix', description='Changes the Bot\'s Prefix. Must have Manage Server.')
    @commands.check_any(commands.has_guild_permissions(manage_guild=True), is_owner())
    @commands.guild_only()
    async def change_prefix(self, ctx, to_change: str = None):
        """
        Changes the prefix for the current guild

        Can only be ran in a guild. If no prefix is specified, will show the current prefix.
        """
        guild_id = str(ctx.guild.id)
        if to_change is None:
            if guild_id in self.bot.prefixes:
                prefix = self.bot.prefixes.get(guild_id, self.bot.prefix)
            else:
                dbsearch = await self.bot.mdb['prefixes'].find_one({'guild_id': guild_id})
                if dbsearch is not None:
                    prefix = dbsearch.get('prefix', self.bot.prefix)
                else:
                    prefix = self.bot.prefix
                self.bot.prefixes[guild_id] = prefix
            return await ctx.send(f'No prefix specified to Change. Current Prefix: `{prefix}`')
        else:
            await ctx.bot.mdb['prefixes'].update_one({'guild_id': guild_id},
                                                     {'$set': {'prefix': to_change}}, upsert=True)
            ctx.bot.prefixes[guild_id] = to_change
            return await ctx.send(f'Guild prefix updated to `{to_change}`')


def setup(bot):
    bot.add_cog(Admin(bot))
