import discord
from utils.constants import DM_CATEGORY_PERMS, DM_ALLOWED_PERMS, OTHER_CATEGORY_PERMS, ARCHIVED_PERMS
from utils.functions import get_positivity
import logging


class DMCategory:
    def __init__(self, cog, guild_id: int, category_id: int, owner_id: int, hub_id: int, allowed: list = None,
                 roles: list = None, archived: list = None):
        self.cog = cog
        self.guild = cog.bot.get_guild(guild_id)
        self.category = self.guild.get_channel(category_id)
        self.hub = self.guild.get_channel(hub_id)
        self.owner = cog.bot.get_user(owner_id)
        self.allowed = allowed
        self.roles = roles
        self.archived = archived
        self.update()

    @staticmethod
    def from_dict(cog, data):
        return DMCategory(cog=cog, guild_id=data['guild_id'], category_id=data['cat_id'], owner_id=data['owner'],
                          hub_id=data['hub_id'], allowed=data['allowed'], roles=data['roles'], archived=data['archived']
                          )

    @staticmethod
    def from_ctx(cog, ctx):
        # Need to get the data
        server_data = DMCategory.get_server_data(cog, ctx)
        # Now we have the whole server's data
        data = None
        for category in server_data['categories']:
            if category['owner'] == ctx.author.id:
                data = category
        if data is not None:
            return DMCategory.from_dict(cog=cog, data=data)
        else:
            return None

    @staticmethod
    async def create(cog, ctx):
        guild = ctx.guild
        db = cog.db
        data = DMCategory.get_server_data(cog, ctx)
        for category in data['categories']:
            if category['owner'] == ctx.author.id:
                return -1
        overwrites = {
            ctx.author: DM_CATEGORY_PERMS,
            guild.default_role: OTHER_CATEGORY_PERMS
        }
        new_cat = await guild.create_category(name=f'{ctx.author.display_name}\'s Category', overwrites=overwrites)
        dm_hub = await guild.create_text_channel(name=f'dm-hub-{str(new_cat.id)[::8]}', category=new_cat)
        category_data = {
            "cat_id": new_cat.id,
            "owner": ctx.author.id,
            "hub_id": dm_hub.id,
            "allowed": [],
            "roles": [],
            "archived": [],
            "guild_id": ctx.guild.id
        }
        data['categories'].append(category_data)
        category = DMCategory.from_dict(cog, category_data)
        await category.hub.send('Welcome to your new DM channel! First thing I\'d recommend changing is the name.\n'
                                'The only people who can see this channel are you, the server owner, and the bot.')
        return category

    @staticmethod
    def get_server_data(cog, ctx):
        db = cog.db
        server = db.find_one({'_id': ctx.guild.id})
        if server is None:
            base = {'_id': ctx.guild.id, 'categories': []}
            db.insert_one(base)
            server_data = base
        else:
            server_data = server
        return server_data

    def to_dict(self):
        return {
            "cat_id": self.category.id,
            "owner": self.owner.id,
            "hub_id": self.hub.id,
            "allowed": self.allowed,
            "roles": self.roles,
            "archived": self.archived,
            "guild_id": self.guild.id
        }

    async def delete(self, ctx):
        cat_data = self.to_dict()
        server_data = self.get_server_data(self.cog, ctx)

        author = ctx.author
        channel = ctx.channel

        def chk(m):
            return m.author == author and m.channel == channel

        await ctx.send('WARNING: This action is **irreversible**. Please confirm that you want to do this. (yes or no)')
        response = await self.cog.bot.wait_for('message', timeout=20, check=chk)
        if get_positivity(response.content):
            if self.category is None:
                return await ctx.author.send('Your DM category does not exist and has been deleted from records.')
            for channel in self.category.channels:
                try:
                    await channel.delete(reason=f'Requested by DM {ctx.author.display_name}')
                except discord.HTTPException:
                    pass
            try:
                await self.category.delete(reason=f'Requested by DM {ctx.author.display_name}')
            except discord.HTTPException:
                pass
            server_data['categories'].remove(cat_data)
            self.update()

        await ctx.author.send('Your DM category has been deleted.')

    def update(self):
        db = self.cog.db
        server_data = db.find_one({'_id': self.guild.id})
        if server_data is not None:
            # Get data from DB if the category id = our id
            cat_old_data = [cat for cat in server_data['categories'] if cat['cat_id'] == self.category.id]
            cat_old_data = cat_old_data[0] if len(cat_old_data) == 1 else None
            # If the data exists
            if cat_old_data:
                # Get the index of the data
                index = server_data['categories'].index(cat_old_data)
                # Replace the old data with the new data
                server_data['categories'][index] = self.to_dict()
            else:
                # If the data doesn't exist, add to DB
                server_data['categories'].append(self.to_dict())
            # Replace data
            db.replace_one({'_id': self.guild.id}, server_data)
        else:
            # If no server, add server with cat data
            db.insert_one({'_id': self.guild.id, 'categories': [self.to_dict()]})

    async def update_channels(self):
        """Adds role overrides to every RP Channel. This is used when new channels are created."""
        for channel in self.category.channels:
            if channel.id == self.hub.id:  # Skip Hub
                continue
            for role_id in self.roles:
                role = self.guild.get_role(role_id)
                if role is None:
                    self.roles.remove(role_id)
                if channel.id in self.archived:
                    await channel.set_permissions(role, overwrite=ARCHIVED_PERMS)
                else:
                    await channel.set_permissions(role, overwrite=DM_ALLOWED_PERMS)
                await channel.set_permissions(self.owner, overwrite=DM_CATEGORY_PERMS)
        self.update()

    async def allow(self, user_id: int):
        """Allows a user into the DM hub by user id."""
        user = self.cog.bot.get_user(user_id)
        if user.id in self.allowed:
            return -1
        self.allowed.append(user.id)
        await self.hub.set_permissions(user, overwrite=DM_ALLOWED_PERMS)
        self.update()
        return 0

    async def deny(self, user_id: int):
        """Removes a user from the DM hub by user id."""
        user = self.cog.bot.get_user(user_id)
        if user.id not in self.allowed:
            return -1
        self.allowed.remove(user.id)
        await self.hub.set_permissions(user, overwrite=None)
        self.update()

    async def add_role(self, role: discord.Role):
        """Adds a role to every current RP Channel"""
        if role.id in self.roles:
            return -1
        self.roles.append(role.id)
        for channel in self.category.channels:
            if channel.id == self.hub.id:  # Skip Hub
                continue
            if channel.id in self.archived:
                await channel.set_permissions(role, overwrite=ARCHIVED_PERMS)
            else:
                await channel.set_permissions(role, overwrite=DM_ALLOWED_PERMS)
        self.update()

    async def remove_role(self, role: discord.Role):
        """Removes a role from every current RP channel."""
        if role.id not in self.roles:
            return -1
        self.roles.remove(role.id)
        for channel in self.category.channels:
            if channel.id == self.hub.id:  # Skip Hub
                continue
            await channel.set_permissions(role, overwrite=None)
        self.update()

    async def archive(self, channel: discord.TextChannel):
        if channel.id in self.archived:
            return -1
        self.archived.append(channel.id)
        await self.update_channels()

    async def unarchive(self, channel: discord.TextChannel):
        if channel.id not in self.archived:
            return -1
        self.archived.remove(channel.id)
        await self.update_channels()

    def __str__(self):
        return f'DMCategory | Server: {self.guild.name} | Category: {self.category.name} | Hub Channel: {self.hub.name}'
