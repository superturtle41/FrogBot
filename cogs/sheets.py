from discord.ext import commands
import discord
from .models.sheet_errors import NoApprover, NoChannel, NoGuild, NoMessage, NoOwner


class Approval:
    def __init__(self, approver: discord.Member, guild: discord.Guild):
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
                 message: discord.Message, approvals: list[Approval]):
        self._owner = owner
        self._guild = guild
        self._channel = channel,
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

    def to_dict(self):
        return {
            'type': 'sheet',
            'owner_id': self.owner.id,
            'guild_id': self.guild.id,
            'channel_id': self.channel.id,
            'message_id': self.message.id,
            'approvals': [a.to_dict() for a in self.approvals]
        }

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


class SheetApproval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_db = bot.mdb['sheet-approval-settings']
        self.sheets_db = bot.mdb['sheet-approvals']

    @commands.group(name='sheet', invoke_without_command=True)
    async def sheet(self, ctx, *, content: str):
        """
        Create a new sheet.
        """
        pass

    @sheet.command(name='setup')
    async def sheet_setup(self, ctx, setting: str, value):
        """
        Commands to setup the Sheet Approval functions.
        Valid settings:
        `sheet-channel <channel>` - Sets the channel to watch for new sheets.
        Will delete any messages that are not sheets in this channel
        `approved-channel <channel>` - Sets the channel to post the sheet approved message.
        `approved-role <role mention>` - Sets the role to add when a player is approved.
        `new-role <role mention>` - Sets the role to removed when a player is approved.
        `approvals <number of approvals> - Sets the number of approvals required to approve a sheet
        """
        if setting == 'sheet-channel':
            pass
        elif setting == 'approved-channel':
            pass
        elif setting == 'approved-role':
            pass
        elif setting == 'new-role':
            pass
        elif setting == 'approvals':
            pass
        else:
            return await ctx.send(f'Invalid setting `{setting}`\nCheck the help for valid settings\nCase Sensitive!')


def setup(bot):
    bot.add_cog(SheetApproval(bot))
