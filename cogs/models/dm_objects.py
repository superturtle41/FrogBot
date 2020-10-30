from discord import Member, CategoryChannel, Guild, TextChannel
from .dm_constants import *


class InvalidArgument(Exception):
    pass


class DMCategory:
    def __init__(self, owner: Member, category: CategoryChannel, guild: Guild, channels: list):
        self._owner = owner
        self._category = category
        self._guild = guild
        self._channels = channels

    @classmethod
    def from_dict(cls, bot, data):
        if not isinstance(data['guild'], int):
            raise InvalidArgument('Guild ID must be an Int.')
        guild = bot.get_guild(data['guild'])
        if guild is None:
            raise InvalidArgument('Guild must exist.')
        if not isinstance(data['owner_id'], int):
            raise InvalidArgument('Owner ID must be an int.')
        owner = guild.get_member(data['owner_id'])
        if owner is None:
            raise InvalidArgument('Owner must exist.')
        if not isinstance(data['category_id'], int):
            raise InvalidArgument('Category ID must be an int.')
        category = guild.get_channel(data['category_id'])
        if category is None:
            raise InvalidArgument('Category must exist.')
        this = cls(owner, category, guild, channels=[])
        channels = [DMChannel.from_dict(this, x) for x in data['channels']]
        this.channels = channels
        return this

    def to_dict(self):
        return {
            'owner_id': self.owner.id,
            'category_id': self.category.id,
            'guild_id': self.guild.id,
            'channels': [x.to_dict() for x in self.channels]
        }

    @property
    def guild(self):
        return self._guild

    @property
    def owner(self):
        return self._owner

    @property
    def category(self):
        return self._category

    @property
    def channels(self):
        return self._channels

    @channels.setter
    def channels(self, new_channels):
        self._channels = new_channels


class DMChannel:
    def __init__(self, category: DMCategory, permissions: list, channel: discord.TextChannel):
        self._category = category
        self._permissions = permissions
        self._channel = channel

    @classmethod
    def from_dict(cls, category, data: dict):
        if not isinstance(data['channel_id'], int):
            raise InvalidArgument('Channel ID must be an int.')
        channel = category.guild.get_channel(data['channel_id'])
        if channel is None:
            raise InvalidArgument('Channel must exist.')
        permissions = [DMPermissions.from_dict(category.guild, x) for x in data['permissions']]
        return cls(category, permissions, channel)

    def to_dict(self):
        return {'channel_id': self.channel.id, 'permissions': [p.to_dict() for p in self.permissions]}

    @property
    def category(self):
        return self._category

    @property
    def guild(self):
        return self.category.guild

    @property
    def permissions(self):
        return self._permissions

    @property
    def channel(self):
        return self._channel


class DMPermissions:
    def __init__(self, type_: int, obj, perm_type: int, guild: Guild):
        self._type = type_
        self._perm_type = perm_type
        self._obj = obj
        self._obj_type = ['Role', 'Member', 'Everyone'][type_]
        self._perms = [CHANNEL_ADMIN, CHANNEL_READ_WRITE, CHANNEL_READ, CHANNEL_HIDDEN][perm_type]
        self._guild = guild

    @classmethod
    def from_dict(cls, guild: Guild, data: dict):
        if not isinstance(data['type'], int) or not (0 <= data['type'] <= 2):
            raise InvalidArgument('Type must be 0, 1, or 2.')
        type_ = data['type']
        if not isinstance(data['perm_type'], int) or not data['perm_type'] in range(0, 4):
            raise InvalidArgument('Permission Type must be in range 0 - 4.')
        perm_type = data['perm_type']
        obj = None
        if type_ == 0:
            obj = guild.get_role(data['obj_id'])
        elif type_ == 1:
            obj = guild.get_member(data['obj_id'])
        elif type_ == 2:
            obj = guild.default_role
        if obj is None:
            raise InvalidArgument('Could not find object that this item applies too.')
        return cls(type_, obj, perm_type, guild)

    def to_dict(self):
        return {
            'type': self._type,
            'perm_type': self.object_type,
            'obj_id': self.applies_to.id
        }

    @property
    def permissions(self):
        return self._perms

    @property
    def object_type(self):
        return self._obj_type

    @property
    def applies_to(self):
        return self._obj

    @property
    def guild(self):
        return self._guild

    def apply_to(self, channel):
        if self.object_type == 'Everyone':
            await channel.set_permissions(self.guild.default_role, overwrite=self.permission)
        else:
            await channel.set_permissions(self.applies_to, overwrite=self.permissions)
