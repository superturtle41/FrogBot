import logging

from discord.ext import commands
from discord.ext import menus

from utils.errors import InvalidArgument
from utils.checks import is_owner, is_authorized
from utils.functions import create_default_embed

log = logging.getLogger(__name__)


class CommandMenu(menus.ListPageSource):
    def __init__(self, data, ctx):
        super().__init__(data, per_page=20)
        self.context = ctx

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = create_default_embed(self.context)
        message = '\n'.join([f':white_small_square: `{cc.name}`' for _, cc in enumerate(entries, start=offset)])
        if message == '':
            message = 'No custom commands found for this server'
        embed.description = '**Current Custom Commands for this Server**:\n' + message
        return embed


class CustomCommand:
    def __init__(self, owner_id: int, guild_id: int, name: str, content: str):
        """
        """
        self.owner_id = owner_id
        self.guild_id = guild_id
        self.name = name
        self.content = content

    @classmethod
    def from_dict(cls, data):
        return cls(
            owner_id=data['owner_id'],
            guild_id=data['guild_id'],
            name=data['name'],
            content=data['content']
        )

    def to_dict(self):
        return {
            'owner_id': self.owner_id,
            'guild_id': self.guild_id,
            'name': self.name,
            'content': self.content
        }

    @classmethod
    async def new(cls, bot, owner_id: int, guild_id: int, name: str, content: str):
        # Existing Checks
        exists = await bot.mdb['custom_commands'].find_one({'guild_id': guild_id, 'name': name})
        if exists is not None:
            raise InvalidArgument(f'Custom Command with name `{name}` already exists in this guild.')
        # Length Checks
        if len(content) > 2048:
            raise InvalidArgument('Content must be less than 2048 characters.')
        # Create in DB and return
        command = CustomCommand(owner_id, guild_id, name, content)
        await bot.mdb['custom_commands'].insert_one(command.to_dict())
        return command

    async def commit(self, db):
        return await db.update_one(
            {'owner_id': self.owner_id, 'guild_id': self.guild_id},
            {'$set': self.to_dict()},
            upsert=True
        )


class CustomCommands(commands.Cog, name='CustomCommands'):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.mdb['custom_commands']

    async def cog_check(self, ctx):
        return ctx.guild is not None

    async def run_custom_commands(self, ctx):
        if ctx.guild is None:
            return

        cc = await self.db.find_one({'guild_id': ctx.guild_id, 'name': ctx.invoked_with})
        if cc is None:
            return
        cc = CustomCommand.from_dict(cc)
        return await ctx.send(cc.content)

    @commands.group(name='cc', invoke_without_command=True)
    @commands.check_any(commands.has_any_role('DM', 'Dragonspeaker'), is_authorized())
    async def cc_base(self, ctx):
        """
        Base command for CustomCommand commands. Will list any custom commands for this server.
        Any of these commands require the "DM" or "Dragonspeaker" role.
        """
        aliases = await self.db.find({'guild_id': ctx.guild.id}).to_list(None)
        source = CommandMenu(data=[CustomCommand.from_dict(a) for a in aliases], ctx=ctx)
        cc_list = menus.MenuPages(source=source, clear_reactions_after=True)
        await cc_list.start(ctx)

    @cc_base.command(name='create')
    async def cc_create(self, ctx, name: str, *, content: str):
        """
        Create a new Custom Command.
        """
        try:
            new_cc = await CustomCommand.new(self.bot,
                                             owner_id=ctx.author.id,
                                             guild_id=ctx.guild_id,
                                             name=name,
                                             content=content)
        except InvalidArgument as e:
            return await ctx.send(f'Encountered an error while creating the command:\n{str(e)}')
        return await ctx.send(f'Created new command with name `{new_cc.name}`')

    @cc_base.command(name='delete')
    async def cc_delete(self, ctx, name: str):
        """
        Deletes a Custom Counter. The name must be an existing CC.
        """
        cc_dict = await self.db.find_one({'guild_id': ctx.guild_id, 'name': name})
        if cc_dict is None:
            return await ctx.send(f'No CC with name `{name}` found.')
        await self.db.delete_one({'guild_id': ctx.guild_id, 'name': name})
        return await ctx.send(f'Deleted CC with name `{name}` from the server.')


def setup(bot):
    bot.add_cog(CustomCommands(bot))
