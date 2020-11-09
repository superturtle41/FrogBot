from discord.ext import commands
import discord
from utils.errors import InvalidArgument
import logging

log = logging.getLogger(__name__)


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
        exists = bot.mdb['custom_commands'].find_one({'guild_id': guild_id, 'name': name})
        if exists:
            raise InvalidArgument(f'Custom Command with name `{name}` already exists in this guild.')
        # Length Checks
        if len(content) > 2048:
            raise InvalidArgument('Content must be less than 2048 characters.')
        # Create in DB and return
        command = CustomCommand(owner_id, guild_id)
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
        self.ccs = {}

    async def cog_check(self, ctx):
        return ctx.guild is not None

    async def run_custom_commands(self, ctx):
        if ctx.guild is None:
            return
        # TODO: Custom Command Invocation


def setup(bot):
    bot.add_cog(CustomCommands(bot))
