import discord
import utils.checks as checks
from discord.ext import commands
from utils.functions import get_positivity


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
        # example_structure = {'_id': SERVER_ID, 'categories': {'CAT_ID': {'owner': OWNER_ID}}}

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

        exists = False
        cat_id = None
        for category_id in data['categories']:
            if data['categories'][category_id]['owner'] == ctx.author.id:
                exists = True
                cat_id = category_id
        if not exists:
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
        guild = ctx.guild
        data = self.get_server(guild.id)

        exists = False
        hud_id = None
        cat_id = None
        for category_id in data['categories']:
            if data['categories'][category_id]['owner'] == ctx.author.id and 'hub_id' in data['categories'][
                category_id]:
                exists = True
                hud_id = data['categories'][category_id]['hub_id']
                cat_id = category_id
        if not exists:
            return await ctx.send('No DM hub stored in records.')
        if mem.id in data['categories'][cat_id]['allowed']:
            return await ctx.send('Member already on allowed list.')

        channel = guild.get_channel(int(hud_id))
        if channel is None:
            return await ctx.send('DM Channel not found, report to owner of bot.')
        if mem is None:
            return await ctx.send('The person you would like to allow (mention) is the only required argument.')
        await channel.set_permissions(mem, overwrite=self.DM_ALLOWED_PERMS,
                                      reason=f'Requested by {ctx.author.display_name}')
        data['categories'][cat_id]['allowed'].append(mem.id)
        self.update(guild.id, data)
        await ctx.send(f'{mem.display_name} added to your hub channel.')

    @dm_group.command(name='deny', description='Remove a member from your DM channel.')
    async def dm_hub_deny(self, ctx, mem: discord.Member = None):
        """Deny a user into a DM hub by adding their perms."""
        guild = ctx.guild
        data = self.get_server(guild.id)

        exists = False
        hud_id = None
        cat_id = None
        for category_id in data['categories']:
            if data['categories'][category_id]['owner'] == ctx.author.id \
                    and 'hub_id' in data['categories'][category_id]:
                exists = True
                hud_id = data['categories'][category_id]['hub_id']
                cat_id = category_id
        if not exists:
            return await ctx.send('No DM hub stored in records.')
        if mem.id not in data['categories'][cat_id]['allowed']:
            return await ctx.send('Member not on allowed list.')

        channel = guild.get_channel(int(hud_id))
        if channel is None:
            return await ctx.send('DM Channel not found, report to owner of bot.')
        if mem is None:
            return await ctx.send('The person you would like to remove (mention) is the only required argument.')
        await channel.set_permissions(mem, overwrite=None, reason=f'Requested by {ctx.author.display_name}')
        data['categories'][cat_id]['allowed'].remove(mem.id)
        self.update(guild.id, data)
        await ctx.send(f'{mem.display_name} removed from your hub channel.')

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
        data = self.get_server(ctx.guild.id)
        category_id = self.get_cat_id(ctx.guild, ctx.author)
        if not category_id:
            return await ctx.send('No DM category stored in records.')
        if role.id in data['categories'][category_id]['roles']:
            return await ctx.send('Role already in list. Update to apply to new channels.')
        data['categories'][category_id]['roles'].append(role.id)
        self.update(ctx.guild.id, data)
        category = ctx.guild.get_channel(int(category_id))
        if not category:
            return await ctx.send('No DM category stored in records.')
        for channel in category.channels:
            if channel.id == data['categories'][category_id]['hub_id']:  # Skip Hub
                continue
            await channel.set_permissions(role, overwrite=self.DM_ALLOWED_PERMS,
                                          reason=f'Requested by {ctx.author.display_name}')
        await ctx.send(f'Added Role {role.mention} to your RP channels (not your hub).')

    @dm_group.command(name='removerole', description='Removes a quest role to all current channels.')
    async def dm_all_removerole(self, ctx, role: discord.Role):
        data = self.get_server(ctx.guild.id)
        category_id = self.get_cat_id(ctx.guild, ctx.author)
        if not category_id:
            return await ctx.send('No DM category stored in records.')
        if role.id not in data['categories'][category_id]['roles']:
            return await ctx.send('Role not in existing lists.')
        data['categories'][category_id]['roles'].remove(role.id)
        self.update(ctx.guild.id, data)
        category = ctx.guild.get_channel(int(category_id))
        if not category:
            return await ctx.send('No DM category stored in records.')
        for channel in category.channels:
            if channel.id == data['categories'][category_id]['hub_id']:  # Skip Hub
                continue
            await channel.set_permissions(role, overwrite=None,
                                          reason=f'Requested by {ctx.author.display_name}')
        await ctx.send(f'Removed role {role.mention} from your RP channels (not your hub).')

    @dm_group.command(name='updaterole', description='Updates all your channels with current roles.')
    async def dm_all_update(self, ctx):
        data = self.get_server(ctx.guild.id)
        category_id = self.get_cat_id(ctx.guild, ctx.author)
        if not category_id:
            return await ctx.send('No DM category stored in records.')
        category = ctx.guild.get_channel(int(category_id))
        if not category:
            return await ctx.send('No DM category stored in records.')
        for channel in category.channels:
            if channel.id == data['categories'][category_id]['hub_id']:  # Skip Hub
                continue
            for role_id in data['categories'][category_id]['roles']:
                role = discord.get_role(role_id)
                if role is None:
                    continue
                await channel.set_permissions(role, overwrite=self.DM_ALLOWED_PERMS, reason=f'Requested by {ctx.author.display_name}')
        await ctx.send(f'Updated roles for your RP channels (not your hub).')

    @dm_group.command(name='listroles', description='List current roles allowed in RP channels.')
    async def dm_all_listroles(self, ctx):
        data = self.get_server(ctx.guild.id)
        category_id = self.get_cat_id(ctx.guild, ctx.author)
        if not category_id:
            return await ctx.send('No DM category stored in records.')
        category = ctx.guild.get_channel(int(category_id))
        if not category:
            return await ctx.send('No DM category stored in records.')
        message = 'Allowed Roles in your RP channels:\n'
        for channel in category.channels:
            if channel.id == data['categories'][category_id]['hub_id']:  # Skip Hub
                continue
            for role_id in data['categories'][category_id]['roles']:
                role = discord.get_role(role_id)
                if role is None:
                    continue
                message += f'<:white_medium_small_square:746529103233941514> {role.mention}\n'
        await ctx.send(message)


def setup(bot):
    bot.add_cog(QuestChannels(bot))
