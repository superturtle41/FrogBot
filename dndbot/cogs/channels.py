import discord
import utils.checks as checks
from discord.ext import commands
from utils.functions import get_positivity
import logging

log = logging.getLogger('channels')

class DMCategory:
    def __init__(self, cog, guild_id: int, category_id: int, owner_id: int, hub_id: int, allowed: list = None,
                 roles: list = None):
        self.cog = cog
        self.guild = cog.bot.get_guild(guild_id)
        self.category = self.guild.get_channel(category_id)
        self.hub = self.guild.get_channel(hub_id)
        self.owner = cog.bot.get_user(owner_id)
        self.allowed = allowed
        self.roles = roles
        self.DM_CATEGORY_PERMS = discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            manage_channels=True
        )
        self.DM_ALLOWED_PERMS = discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True
        )
        self.OTHER_CATEGORY_PERMS = discord.PermissionOverwrite(
            read_messages=False,
            send_messages=False
        )
        self.update()

    @staticmethod
    def from_dict(cog, guild_id: int, data: dict):
        # data = {'CAT_ID': {'owner': OWNER_ID, 'hub_id': HUB_CHANNEL_ID, 'allowed': [USER_ID], 'roles': [ROLE_ID]}}
        category_id = int(list(data.keys())[0])
        spec = data[str(category_id)]
        return DMCategory(cog=cog, guild_id=guild_id, category_id=category_id, hub_id=spec['hub_id'],
                          owner_id=spec['owner'], allowed=spec['allowed'], roles=spec['roles'])

    @staticmethod
    def from_ctx(ctx, cog):
        # Need to get the data
        db = cog.db
        server = db.find_one({'_id': ctx.guild.id})
        if server is None:
            base = {'_id': ctx.guild.id, 'categories': {}}
            db.insert_one(base)
            server_data = base
        else:
            server_data = server
        # Now we have the whole server's data
        exists = False
        cat_id = None
        for category in server_data['categories']:
            if server_data['categories'][category]['owner'] == ctx.author.id:
                exists = True
                cat_id = int(category)
        if exists:
            data = {str(cat_id): server_data['categories'][str(cat_id)]}
        else:
            return None

        return DMCategory.from_dict(cog=cog, guild_id=ctx.guild.id, data=data)

    def update(self):
        db = self.cog.db
        server_data = db.find_one({'_id': self.guild.id})
        if server_data is not None:
            server_data['categories'][str(self.category.id)] = self.to_dict()
            db.replace_one({'_id': self.guild.id}, server_data)
        else:
            db.insert_one({'_id': self.guild.id, 'categories': {
                {str(self.category.id): self.to_dict()}
            }})

    def to_dict(self):
        return {'owner': self.owner.id,
                'hub_id': self.hub.id,
                'allowed': self.allowed,
                'roles': self.roles
                }

    async def update_channels(self):
        """Adds role overrides to every RP Channel. This is used when new channels are created."""
        for channel in self.category.channels:
            if channel.id == self.hub.id:  # Skip Hub
                continue
            for role_id in self.roles:
                role = self.guild.get_role(role_id)
                if role is None:
                    self.roles.remove(role_id)
                await channel.set_permissions(role, overwrite=self.DM_ALLOWED_PERMS)
        self.update()

    async def allow(self, user_id: int):
        """Allows a user into the DM hub by user id."""
        user = self.cog.bot.get_user(user_id)
        if user.id in self.allowed:
            return -1
        self.allowed.append(user.id)
        await self.hub.set_permissions(user, overwrite=self.DM_ALLOWED_PERMS)
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
            await channel.set_permissions(role, overwrite=self.DM_ALLOWED_PERMS)
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

    def __str__(self):
        return f'DMCategory | Server: {self.guild.name} | Category: {self.category.name} | Hub Channel: {self.hub.name}'


class QuestChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.mdb['quest-channels']
        self.DM_CATEGORY_PERMS = discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            manage_channels=True
        )
        self.DM_ALLOWED_PERMS = discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True
        )
        self.OTHER_CATEGORY_PERMS = discord.PermissionOverwrite(
            read_messages=False,
            send_messages=False
        )

    def get_server(self, server_id):
        """Returns the server from the database."""
        server = self.db.find_one({'_id': server_id})
        if server is None:
            base = {'_id': server_id, 'categories': {}}
            self.db.insert_one(base)
            return base
        else:
            return server

    def update(self, server_id, data: dict):
        server = self.db.find_one({'_id': server_id})
        if server is not None:
            self.db.replace_one({'_id': server_id}, data)

    def get_cat_id(self, guild, owner):
        data = self.get_server(guild.id)

        exists = False
        cat_id = None
        for category_id in data['categories']:
            if data['categories'][category_id]['owner'] == owner.id and 'hub_id' in data['categories'][category_id]:
                exists = True
                cat_id = category_id
        if not exists:
            return None
        return cat_id

    def get_hub_from_cat(self, guild, cat_id):
        data = self.get_server(guild.id)
        if str(cat_id) in data['categories'] and 'hub_id' in data['categories'][str(cat_id)]:
            return data['categories'][str(cat_id)]['hub_id']
        else:
            return False

    @commands.group(name='dm', description='Base command for all other DM Channel commands.'
                                           ' All subcommands require DM role.')
    @checks.is_dm()
    async def dm_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid Sub-command passed')

    @dm_group.command(name='setup', description='Sets up a DM Category.')
    async def dm_setup(self, ctx):
        guild = ctx.guild
        data = self.get_server(guild.id)
        for category_id in data['categories']:
            if data['categories'][category_id]['owner'] == ctx.author.id:
                return await ctx.send('DM Category has already been setup.')
        overwrites = {
            ctx.author: self.DM_CATEGORY_PERMS,
            guild.default_role: self.OTHER_CATEGORY_PERMS
        }
        new_cat = await guild.create_category(name=f'{ctx.author.display_name}\'s Category', overwrites=overwrites)
        dm_hub = await guild.create_text_channel(name=f'dm-hub-{str(new_cat.id)[::8]}', category=new_cat)
        data['categories'][str(new_cat.id)] = {'owner': ctx.author.id, 'hub_id': dm_hub.id, 'allowed': [], 'roles': []}
        self.update(guild.id, data)
        await ctx.send('DM category created.')
        await dm_hub.send('Welcome to your new DM channel! First thing I\'d recommend changing is the name.\n'
                          'The only people who can see this channel are you, the server owner, and the bot.')

    @dm_group.command(name='delete', description='Deletes a DM category. Requires DM role.')
    async def dm_delete(self, ctx):
        guild = ctx.guild
        data = self.get_server(guild.id)

        author = ctx.author
        channel = ctx.channel

        def chk(m):
            return m.author == author and m.channel == channel

        cat_id = self.get_cat_id(guild, author)
        if not cat_id:
            return await ctx.send('No DM category stored in records.')

        category = guild.get_channel(int(cat_id))

        await ctx.send('WARNING: This action is **irreversible**. Please confirm that you want to do this. (yes or no)')
        response = await self.bot.wait_for('message', timeout=20, check=chk)
        if get_positivity(response.content):
            if category is None:
                return await ctx.author.send('Your DM category does not exist and has been deleted from records.')
            for channel in category.channels:
                await channel.delete(reason=f'Requested by DM {ctx.author.display_name}')
            await category.delete(reason=f'Requested by DM {ctx.author.display_name}')
            data['categories'].pop(str(cat_id))
            self.update(guild.id, data)
        await ctx.author.send('Your DM category has been deleted.')

    @dm_group.command(name='allow', description='Allow a member to your DM channel.')
    async def dm_hub_allow(self, ctx, mem: discord.Member = None):
        """Allow a user into a DM hub by adding their perms."""
        cat = DMCategory.from_ctx(ctx, self)
        if cat is None:
            return await ctx.send('Category does not exist')
        result = await cat.allow(mem.id)
        if result == -1:
            return await ctx.send(f'User already in allowed list.')
        await ctx.send(f'Added {mem.display_name} to your DM Hub.')

    @dm_group.command(name='deny', description='Remove a member from your DM channel.')
    async def dm_hub_deny(self, ctx, mem: discord.Member = None):
        """Deny a user from a DM hub by removing their perms."""
        cat = DMCategory.from_ctx(ctx, self)
        if cat is None:
            return await ctx.send('Category does not exist')
        result = await cat.deny(mem.id)
        if result == -1:
            return await ctx.send(f'User not in allowed list.')
        await ctx.send(f'Removed {mem.display_name} to your DM Hub.')

    @dm_group.command(name='list', description='List allowed people in your channel.')
    async def dm_hub_list(self, ctx):
        data = self.get_server(ctx.guild.id)
        category_id = self.get_cat_id(ctx.guild, ctx.author)
        if not category_id:
            return await ctx.send('No DM hub stored in records.')
        message = 'Allowed Members in your hub channel:\n'
        for member_id in data['categories'][category_id]['allowed']:
            member = self.bot.get_user(member_id)
            message += f'<:white_medium_small_square:746529103233941514> {member.display_name}\n'
        await ctx.send(message)

    @dm_group.command(name='addrole', description='Adds a quest role to all current channels.')
    async def dm_all_allowrole(self, ctx, role: discord.Role):
        """Allow a role into RP channels by adding perms."""
        cat = DMCategory.from_ctx(ctx, self)
        if cat is None:
            return await ctx.send('Category does not exist')
        result = await cat.add_role(role)
        if result == -1:
            return await ctx.send(f'Role already in allowed list.')
        await ctx.send(f'Added {role.mention} to your RP channels.')

    @dm_all_allowrole.error
    async def dm_all_allowrole_nf(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Role not found.')

    @dm_group.command(name='removerole', description='Removes a quest role to all current channels.')
    async def dm_all_removerole(self, ctx, role: discord.Role):
        """Remove a role from RP channels by removing perms."""
        cat = DMCategory.from_ctx(ctx, self)
        if cat is None:
            return await ctx.send('Category does not exist')
        result = await cat.remove_role(role)
        if result == -1:
            return await ctx.send(f'Role not in allowed list.')
        await ctx.send(f'Removed {role.mention} from your RP channels.')

    @dm_all_removerole.error
    async def dm_all_removerole_nf(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Role not found.')

    @dm_group.command(name='updaterole', description='Updates all your channels with current roles.')
    async def dm_all_update(self, ctx):
        """Remove a role from RP channels by removing perms."""
        cat = DMCategory.from_ctx(ctx, self)
        if cat is None:
            return await ctx.send('Category does not exist')
        await cat.update_channels()
        await ctx.send(f'Updated roles for your RP channels (not your hub).')

    @dm_group.command(name='listroles', description='List current roles allowed in RP channels.')
    async def dm_all_listroles(self, ctx):
        cat = DMCategory.from_ctx(ctx, self)
        if cat is None:
            return await ctx.send('Category does not exist')
        message = 'Allowed Roles in your RP channels:\n'
        for role_id in cat.roles:
            role = ctx.guild.get_role(role_id)
            if role is None:
                continue
            message += f'<:white_medium_small_square:746529103233941514> {role.mention}\n'
        await ctx.send(message)

    @dm_group.command(name='test', hidden=True)
    @checks.is_owner()
    async def dm_test(self, ctx):
        data = self.get_server(ctx.guild.id)
        cat_id = self.get_cat_id(ctx.guild, ctx.author)
        if cat_id is None:
            return await ctx.send('No category found in this server.')
        cat = DMCategory.from_dict(self, ctx.guild.id, {str(cat_id): data['categories'][str(cat_id)]})
        await ctx.send(cat)


def setup(bot):
    bot.add_cog(QuestChannels(bot))
