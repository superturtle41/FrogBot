from discord.ext import commands
import discord
from .models.sheet_errors import NoApprover, NoChannel, NoGuild, NoMessage, NoOwner, SheetError
from utils.functions import create_default_embed
from utils.checks import can_change_sheet_settings
from utils.constants import ABLE_TO_APPROVE, SETTINGS_CHANGE


class EmojiContext:
    def __init__(self, guild, channel, message, member):
        self.guild = guild
        self.channel = channel
        self.message = message
        self.owner = member

    @classmethod
    async def from_payload(cls, bot, data):
        """
        :param bot: The bot to use to get the data from
        :param data: Payload Data - Must be a guild reaction
        :return: EmojiContext or None
        """
        if data.guild_id is None:
            return None
        guild = bot.get_guild(data.guild_id)
        channel = guild.get_channel(data.channel_id)
        member = guild.get_member(data.user_id)
        message = await channel.fetch_message(data.message_id)
        return cls(guild=guild, channel=channel, message=message, member=member)


class Approval:
    def __init__(self, approver: discord.Member, guild: discord.Guild):
        """
        Represents an approval on a sheet.
        :param approver: The member who is approving
        :type: discord.Member
        :param guild:
        :type: discord.Guild
        """
        self._approver = approver
        self._guild = guild

    @property
    def approver(self):
        return self._approver

    @property
    def guild(self):
        return self._guild

    @classmethod
    async def from_dict(cls, bot, data):
        """
        Takes a database object and converts it to an approval
        :param bot: Bot to get the guild from
        :param data: Data containing the guild id and member id.
        :return: Approval
        """
        guild = bot.get_guild(data['guild_id'])
        if guild is None:
            raise NoGuild('Guild does not exist.')
        member = guild.get_member(data['member_id'])
        if member is None:
            raise NoApprover('Approver does not exist.')
        return cls(member, guild)

    def to_dict(self):
        return {
            'type': 'approval',
            'member_id': self.approver.id,
            'guild_id': self.guild.id
        }


class Sheet:
    def __init__(self, owner: discord.Member, guild: discord.Guild, channel: discord.TextChannel,
                 message: discord.Message, approvals: list):
        """
        An object representing a Sheet to approve.
        :param owner: Owner of the Sheet
        :type: discord.Member
        :param guild: Guild in which the sheet resides in.
        :type: discord.Guild
        :param channel: The Channel in which the sheet was sent. Used for fetching messages.
        :type: discord.TextChannel
        :param message: The actual message of the sheet containing the embed.
        :type: discord.Message
        :param approvals: List of approvals for the sheet.
        :type: list[Approval]
        """
        self._owner = owner
        self._guild = guild
        self._channel = channel
        self._message = message
        self._approvals = approvals

    @classmethod
    async def from_dict(cls, bot, data):
        guild = bot.get_guild(data['guild_id'])
        if guild is None:
            raise NoGuild('Guild does not exist.')
        member = guild.get_member(data['member_id'])
        if member is None:
            raise NoOwner('Owner does not exist.')
        channel: discord.TextChannel = guild.get_channel(data['channel_id'])
        if channel is None:
            raise NoChannel('Channel does not exist.')
        message = await channel.fetch_message(data['message_id'])
        if message is None:
            raise NoMessage('Message does not exist')
        approvals = []
        for raw_approval in data['approvals']:
            approvals.append(Approval.from_dict(bot, raw_approval))
        return cls(owner=member, guild=guild, channel=channel, message=message, approvals=approvals)

    @classmethod
    async def new_from_ctx(cls, ctx, content):
        """
        Takes in the context and the content, and creates a new sheet.
        :param ctx: Context to use
        :param content: Content of sheet.
        :return: Sheet
        """
        # Send Message
        embed = create_default_embed(ctx)
        embed.title = f'Sheet Approval - {ctx.author.display_name}'
        embed.description = content

        msg = await ctx.send(embed=embed)
        return Sheet(
            owner=ctx.author,
            guild=ctx.guild,
            channel=ctx.channel,
            message=msg,
            approvals=[]
        )

    @classmethod
    async def from_emoji_context(cls, bot, db, ctx: EmojiContext):
        """
        :param bot: The bot to use to fetch the models from.
        :param db: Database to fetch information from
        :param ctx: EmojiContext to use to query DB
        :return: Sheet or None
        """
        data = await db.find_one({'guild_id': ctx.guild.id, 'message_id': ctx.message.id})
        if data is None:
            return None
        return cls.from_dict(bot, data)

    def to_dict(self):
        return {
            'type': 'sheet',
            'owner_id': self.owner.id,
            'guild_id': self.guild.id,
            'channel_id': self.channel.id,
            'message_id': self.message.id,
            'approvals': [a.to_dict() for a in self.approvals]
        }

    async def save(self, db, upsert=True):
        await db.update_one({'guild_id': self.guild.id, 'message_id': self.message.id},
                            {'$set': self.to_dict()},
                            upsert=upsert)

    @property
    def owner(self):
        return self._owner

    @property
    def guild(self):
        return self._guild

    @property
    def channel(self):
        return self._channel

    @property
    def message(self):
        return self._message

    @property
    def approvals(self):
        return self._approvals

    @approvals.setter
    def approvals(self, value):
        self._approvals = value


async def convert_catch_error(converter, ctx, obj, error):
    """
    Takes a converter and trie to convert something, returning None on an error
    :param converter:
    :param ctx: Context to convert with
    :param obj: The object to convert - Usually string
    :param error: The error to ignore.
    :return: Converted Object or None
    """
    try:
        new = await converter.convert(ctx, str(obj))
    except error:
        return None
    return new


class SheetApproval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_db = bot.mdb['sheet-approval-settings']
        self.sheets_db = bot.mdb['sheet-approvals']
        self.channel_converter = commands.TextChannelConverter()
        self.role_converter = commands.RoleConverter()
        self.settings = {'sheet-channel', 'approved-channel', 'approved-role', 'new-role', 'approvals'}

    async def cog_check(self, ctx):
        return ctx.guild_id is not None

    async def server_has_settings(self, guild_id):
        db_settings = await self.settings_db.find_one({'guild_id': guild_id})
        if db_settings is None:
            return False
        for setting in self.settings:
            if setting == 'approvals':
                continue
            if setting not in db_settings:
                return False
        return True

    @commands.Cog.listener('on_raw_reaction_add')
    async def check_for_approval(self, payload):
        context = await EmojiContext.from_payload(self.bot, payload)
        try:
            sheet = await Sheet.from_emoji_context(self.bot, self.sheets_db, context)
        except SheetError:
            return
        if sheet is None:
            return

    @commands.Cog.listener('on_raw_reaction_remove')
    async def check_for_deny(self, payload):
        context = await EmojiContext.from_payload(self.bot, payload)
        try:
            sheet = await Sheet.from_emoji_context(self.bot, self.sheets_db, context)
        except SheetError:
            return
        if sheet is None:
            return

    @commands.group(name='sheet', invoke_without_command=True)
    async def sheet(self, ctx, *, content: str):
        """
        Create a new sheet.
        """
        # Check to make sure all of the settings exist
        if not await self.server_has_settings(ctx.guild_id):
            return await ctx.send('This server does not have all the required settings set up! Contact an administrator'
                                  'for more details.\n(This message will delete itself in 10 seconds.)',
                                  delete_after=10)

        # Create the Sheet Object
        new_sheet = await Sheet.new_from_ctx(ctx, content)
        await new_sheet.save(self.sheets_db)

    @sheet.command(name='setup')
    @can_change_sheet_settings(SETTINGS_CHANGE)
    async def sheet_setup(self, ctx, setting: str, value=''):
        """
        Commands to setup the Sheet Approval functions.
        Returns the current value for the setting if no new value is provided.
        Valid settings:
        `sheet-channel <channel>` - Sets the channel to watch for new sheets.
        Will delete any messages that are not sheets in this channel
        `approved-channel <channel>` - Sets the channel to post the sheet approved message.
        `approved-role <role mention>` - Sets the role to add when a player is approved.
        `new-role <role mention>` - Sets the role to removed when a player is approved.
        `approvals <number of approvals>` - Sets the number of approvals required to approve a sheet
        """

        async def get_setting(guild_id, setting_name):
            db_response = await self.settings_db.find_one({'guild_id': guild_id})
            if db_response is None:
                return None
            if setting_name not in db_response:
                return None
            return db_response[setting_name]

        async def set_setting(guild_id, setting_name, setting_value, upsert=True):
            await self.settings_db.update_one({'guild_id': guild_id},
                                              {'$set': {setting_name: setting_value}}, upsert=upsert)
            return setting_value

        embed = create_default_embed(ctx)
        embed.title = f'Sheet Approval Settings for {ctx.guild.name}'
        if setting == 'sheet-channel':
            if value == '':
                current = await get_setting(ctx.guild.id, 'sheet-channel')
                embed.add_field(name='Sheet Channel', value=f"<#{current}>" if current else "Not set.")
                return await ctx.send(embed=embed)
            channel = await convert_catch_error(self.channel_converter, ctx, value, commands.ChannelNotFound)
            if channel is None:
                embed.add_field(name='Sheet Channel',
                                value=f'Error! Could not find the channel specified with `{value}`.')
                return await ctx.send(embed=embed)
            await set_setting(ctx.guild.id, 'sheet-channel', channel.id)
            embed.add_field(name='Sheet Channel', value=f'The channel for sheets has been set to <#{channel.id}>')
            return await ctx.send(embed=embed)
        elif setting == 'approved-channel':
            if value == '':
                current = await get_setting(ctx.guild.id, 'approved-channel')
                embed.add_field(name='Approval Channel', value=f"<#{current}>" if current else "Not set.")
                return await ctx.send(embed=embed)
            channel = await convert_catch_error(self.channel_converter, ctx, value, commands.ChannelNotFound)
            if channel is None:
                embed.add_field(name='Approval Channel',
                                value=f'Error! Could not find the channel specified with `{value}`.')
                return await ctx.send(embed=embed)
            await set_setting(ctx.guild.id, 'approved-channel', channel.id)
            embed.add_field(name='Approval Channel',
                            value=f'The channel for approval messages has been set to <#{channel.id}>.')
            return await ctx.send(embed=embed)
        elif setting == 'approved-role':
            if value == '':
                current = await get_setting(ctx.guild.id, 'approved-role')
                embed.add_field(name='Approved Role', value=f"<@{current}>" if current else "Not set.")
                return await ctx.send(embed=embed)
            role = await convert_catch_error(self.role_converter, ctx, value, commands.RoleNotFound)
            if role is None:
                embed.add_field(name='Approved Role', value=f'Error! Could not find the role specified with `{value}`.')
                return await ctx.send(embed=embed)
            await set_setting(ctx.guild.id, 'approve-role', role.id)
            embed.add_field(name='Approved Role', value=f'The role for approval has been set to <@{role.id}>')
            return await ctx.send(embed=embed)
        elif setting == 'new-role':
            if value == '':
                current = await get_setting(ctx.guild.id, 'new-role')
                embed.add_field(name='Newb Role', value=f"<@{current}>" if current else "Not set.")
                return await ctx.send(embed=embed)
            role = await convert_catch_error(self.role_converter, ctx, value, commands.RoleNotFound)
            if role is None:
                embed.add_field(name='Newb Role', value=f'Error! Could not find the role specified with `{value}`.')
                return await ctx.send(embed=embed)
            await set_setting(ctx.guild.id, 'new-role', role.id)
            embed.add_field(name='Newb Role', value=f'The role to take from newbs has been set to <@{role.id}>.')
            return await ctx.send(embed=embed)
        elif setting == 'approvals':
            if value == '':
                current = await get_setting(ctx.guild.id, 'approvals')
                embed.add_field(name='# of Approvals', value=str(int(current) if current else 2))
                return await ctx.send(embed=embed)
            try:
                amount = int(value)
            except ValueError:
                embed.add_field(name='# of Approvals', value=f'Error! {value} is not a valid number.')
                return await ctx.send(embed=embed)
            await set_setting(ctx.guild.id, 'approvals', amount)
            embed.add_field(name='# of Approvals', value=f'The number of approvals required has been set to {amount}.')
            return await ctx.send(embed=embed)
        elif setting == 'list':
            for setting in self.settings:
                setting_value = await get_setting(ctx.guild.id, setting)
                embed.add_field(name=setting, value=setting_value if setting_value else 'Not set!')
            return await ctx.send(embed=embed)
        else:
            embed.description = f'Invalid setting `{setting}`\nCheck the help for valid settings (Case Sensitive!)'
            return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SheetApproval(bot))
