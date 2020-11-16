from discord import Member, CategoryChannel, Guild
from utils.errors import InvalidArgument, CategoryExists
from .dm_constants import *


class DMCategory:
    def __init__(self, owner: Member, category: CategoryChannel, guild: Guild, channels: list):
        self._owner = owner
        self._category = category
        self._guild = guild
        self._channels = channels

    @classmethod
    def from_dict(cls, bot, data):
        if not isinstance(data['guild_id'], int):
            raise InvalidArgument('Guild ID must be an Int.')
        guild = bot.get_guild(data['guild_id'])
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
        channels = [channel for channel in channels if channel is not None]
        this.channels = channels
        return this

    def to_dict(self):
        return {
            'owner_id': self.owner.id,
            'category_id': self.category.id,
            'guild_id': self.guild.id,
            'channels': [x.to_dict() for x in self.channels]
        }

    @classmethod
    async def new(cls, bot, guild, owner):
        # Check to make sure User does not already have a DM Category
        db = bot.mdb['dmcategories']
        exists = await db.find_one({'owner_id': owner.id, 'guild_id': guild.id})
        if exists is not None:
            raise CategoryExists('User has an existing category in this server.')
        # Create Default Permissions
        base_perms = {
            guild.me: CHANNEL_ADMIN,
            owner: CHANNEL_ADMIN,
            guild.default_role: CHANNEL_HIDDEN
        }
        # Create Category
        new_category = await guild.create_category(name=f'{owner.display_name}\'s category', overwrites=base_perms)
        new_channel = await guild.create_text_channel(name=f'dm-hub-{owner.display_name}', category=new_category)
        category = DMCategory(owner=owner, category=new_category, guild=guild, channels=[])
        category.channels = [DMChannel(category=category, permissions=[], channel=new_channel)]
        await db.insert_one(category.to_dict())
        return category

    @classmethod
    async def new_from_old(cls, bot, guild, owner, category, hub_channel):
        db = bot.mdb['dmcategories']
        # Create Default Permissions
        base_perms = {
            guild.me: CHANNEL_ADMIN,
            owner: CHANNEL_ADMIN,
            guild.default_role: CHANNEL_HIDDEN
        }
        # Create Category
        new_category = category
        new_channel = hub_channel
        category = DMCategory(owner=owner, category=new_category, guild=guild, channels=[])
        category.channels = [DMChannel(category=category, permissions=[], channel=new_channel)]
        await category.sync_permissions(bot)
        await db.insert_one(category.to_dict())
        return category

    @classmethod
    async def from_ctx(cls, ctx):
        existing = await ctx.bot.mdb['dmcategories'].find_one({'owner_id': ctx.author.id, 'guild_id': ctx.guild.id})
        if existing is not None:
            existing.pop('_id')
            return cls.from_dict(ctx.bot, existing)
        else:
            return None

    async def commit(self, bot):
        await bot.mdb['dmcategories'].update_one({'owner_id': self.owner.id, 'guild_id': self.guild.id},
                                           {'$set': self.to_dict()}, upsert=True)

    async def delete(self, bot):
        to_delete_id = self.category.id

        for channel in self.channels:
            await channel.delete()

        try:
            await self.category.delete()
        except (discord.HTTPException, discord.NotFound):
            pass

        await bot.mdb['dmcategories'].delete_one({'category_id': to_delete_id})

    async def update_channels(self):
        existings = [c.channel.id for c in self.channels]
        new = []
        # Add new channels
        for channel in self.category.channels:
            if channel.id in existings:
                continue
            new_channel = DMChannel(self, [], channel)
            self.channels.append(new_channel), new.append(new_channel)
        return new

    async def sync_permissions(self, bot):
        new = await self.update_channels()
        for channel in self.channels:
            await channel.sync_permissions()
        await self.commit(bot)
        return new

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

    def __str__(self):
        return f"{self.category.name} | {len(self.channels)} channel(s) | {self.category.guild.name}"


class DMChannel:
    def __init__(self, category: DMCategory, permissions: list, channel: discord.TextChannel):
        self._category = category
        self.permissions = permissions
        self._channel = channel

    @classmethod
    def from_dict(cls, category, data: dict):
        if not isinstance(data['channel_id'], int):
            raise InvalidArgument('Channel ID must be an int.')
        channel = category.guild.get_channel(data['channel_id'])
        if channel is None:
            return None
        permissions = [DMPermissions.from_dict(category.guild, x) for x in data['permissions']]
        return cls(category, permissions, channel)

    def to_dict(self):
        return {'channel_id': self.channel.id, 'permissions': [p.to_dict() for p in self.permissions]}

    async def delete(self):
        try:
            await self.channel.delete()
        except (discord.HTTPException, discord.NotFound):
            pass

    async def sync_permissions(self):
        base_perms = {
            self.category.guild.me: CHANNEL_ADMIN,
            self.category.owner: CHANNEL_ADMIN,
            self.category.guild.default_role: CHANNEL_HIDDEN
        }
        await self.channel.edit(sync_permissions=True)
        for perm in self.permissions:
            await perm.apply_permission(self.channel)
        for perm in base_perms:
            await self.channel.set_permissions(perm, overwrite=base_perms[perm])

    async def add_permission(self, perm_to_add):
        intersect = [perm for perm in self.permissions if perm.applies_to.id == perm_to_add.applies_to.id]
        if intersect:
            intersect = intersect[0]
            to_replace = self.permissions.index(intersect)
            self.permissions[to_replace] = perm_to_add
        else:
            self.permissions.append(perm_to_add)
        await self.sync_permissions()

    async def remove_perm_for(self, obj):
        intersect = [perm for perm in self.permissions if perm.applies_to.id == obj.id]
        if intersect:
            intersect = intersect[0]
            to_remove = self.permissions.index(intersect)
            self.permissions.pop(to_remove)
            await self.sync_permissions()
            return True
        else:
            return None


    @property
    def category(self):
        return self._category

    @property
    def guild(self):
        return self.category.guild

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
            'perm_type': self._perm_type,
            'obj_id': self.applies_to.id
        }

    @property
    def permissions(self):
        return self._perms

    @property
    def object_type(self):
        return self._obj_type

    @property
    def raw_object_type(self):
        return self._type

    @property
    def applies_to(self):
        return self._obj

    @property
    def guild(self):
        return self._guild

    @property
    def perm_type(self):
        return ['Admin', 'Read/Send', 'Read-Only', 'Hidden'][self._perm_type]

    async def apply_permission(self, channel):
        await channel.set_permissions(self.applies_to, overwrite=self.permissions)

    def __repl__(self):
        return f'<DMPermissions permissions={self.permissions} applies_to={self.applies_to} type={self.perm_type}>'
