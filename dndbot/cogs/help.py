from discord.ext import commands
import discord
import random
from utils.functions import create_default_embed

# These color constants are taken from discord.js library
colors = {
  'DEFAULT': 0x000000,
  'WHITE': 0xFFFFFF,
  'AQUA': 0x1ABC9C,
  'GREEN': 0x2ECC71,
  'BLUE': 0x3498DB,
  'PURPLE': 0x9B59B6,
  'LUMINOUS_VIVID_PINK': 0xE91E63,
  'GOLD': 0xF1C40F,
  'ORANGE': 0xE67E22,
  'RED': 0xE74C3C,
  'GREY': 0x95A5A6,
  'NAVY': 0x34495E,
  'DARK_AQUA': 0x11806A,
  'DARK_GREEN': 0x1F8B4C,
  'DARK_BLUE': 0x206694,
  'DARK_PURPLE': 0x71368A,
  'DARK_VIVID_PINK': 0xAD1457,
  'DARK_GOLD': 0xC27C0E,
  'DARK_ORANGE': 0xA84300,
  'DARK_RED': 0x992D22,
  'DARK_GREY': 0x979C9F,
  'DARKER_GREY': 0x7F8C8D,
  'LIGHT_GREY': 0xBCC0C0,
  'DARK_NAVY': 0x2C3E50,
  'BLURPLE': 0x7289DA,
  'GREYPLE': 0x99AAB5,
  'DARK_BUT_NOT_BLACK': 0x2C2F33,
  'NOT_QUITE_BLACK': 0x23272A
}


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name='help',
        description='Shows this message',
        aliases=['commands', 'h'],
        usage='cog'
    )
    async def help_command(self, ctx, *args: str):
        help_embed = create_default_embed(self.bot, ctx)
        help_embed.title = '--- Help for Frog Bot ---'
        if len(args) == 0:
            for cog in self.bot.cogs:
                field_value = ""
                for command in self.bot.cogs[cog].get_commands():
                    if command.hidden:
                        continue
                    if not isinstance(command, commands.Group):
                        field_value += f"**{command.qualified_name}** - {command.description}\n"
                        if len(command.aliases) > 0:
                            field_value += f'-- **Aliases:** '
                            for alias in command.aliases:
                                field_value += f'`{alias}` '
                            field_value += "\n"
                    else:
                        field_value += f"**{command.name}** - {command.description}\n"
                        field_value += create_alias_fields(command)
                        for group_command in command.commands:
                            if group_command.hidden:
                                continue
                            field_value += f"**{command.name} {group_command.name}** - {group_command.description}\n"
                            field_value += create_alias_fields(group_command)
                if field_value == '':
                    continue
                help_embed.add_field(name=cog, value=field_value, inline=False)
            await ctx.send(embed=help_embed)
        else:
            raise NotImplementedError('Specific Help has not been implemented yet')
            # Help for one argument. Check to see if argument matches cog, and then command
        return


def create_alias_fields(command) -> str:
    field_value = ""
    if len(command.aliases) > 0:
        field_value += f'-- **Aliases:** '
        for alias in command.aliases:
            field_value += f'`{alias}` '
        field_value += "\n"
    return field_value


def setup(bot):
    bot.add_cog(Help(bot))
