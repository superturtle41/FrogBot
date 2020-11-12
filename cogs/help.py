from discord.ext import commands, menus
from utils.functions import create_default_embed
import discord


class HelpMenu(menus.ListPageSource):
    def __init__(self, data, ctx, embed_title, embed_footer):
        super().__init__(data, per_page=15)
        self.context = ctx
        self.embed_title = embed_title
        self.embed_footer = embed_footer

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = create_default_embed(self.context)
        embed.title = self.embed_title
        embed.set_footer(text=self.embed_footer)
        message = '\n'.join([command for _, command in enumerate(entries, start=offset)])
        message = message + f'\nPage {menu.current_page+1}/{self.get_max_pages()}'
        embed.add_field(name='Commands', value=message)
        return embed


def generate_command_names(command_list, short_doc=False):
    out = []
    for command in command_list:
        parent = (command.full_parent_name + " ") if command.full_parent_name else ""
        name = f'`{parent}{command.name}`'
        if short_doc:
            name += f' - {command.short_doc}'
        if isinstance(command, commands.Group) and len(command.commands):
            name = '__' + name + '__'
        out.append(name)
    return out


class CustomHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        to_send = self.get_destination()
        embed = create_default_embed(self.context)
        embed.title = 'FrogBot Help'
        embed.description = self.cog.bot.description
        for cog in mapping:
            command_list = await self.filter_commands(mapping[cog], sort=True)
            out = []
            for command in command_list:
                name = f'**{command.name}:**'
                if isinstance(command, commands.Group):
                    name = '__' + name + '__'
                out.append(f'{name} {command.short_doc}')
            if len(out) > 0:
                embed.add_field(name=cog.qualified_name, value='\n'.join(out), inline=False)
        embed.set_footer(text=f'An underlined command has subcommands.\n'
                              f'See {self.clean_prefix}help <command name> for more details on individual commands')
        await to_send.send(embed=embed)

    async def send_cog_help(self, cog):
        to_send = self.get_destination()
        embed = create_default_embed(self.context)
        embed.title = f'FrogBot Help - {cog.qualified_name}'
        command_list = await self.filter_commands(cog.get_commands(), sort=True)
        embed.description = cog.description or 'No description specified.'
        out = generate_command_names(command_list)
        if len(out) > 0:
            embed.add_field(name='Commands', value=' '.join(out), inline=False)
        embed.set_footer(text=f'An underlined command has subcommands.\n'
                              f'See {self.clean_prefix}help <command name> for more details '
                              f'on individual commands')
        await to_send.send(embed=embed)

    async def send_group_help(self, group):
        to_send = self.get_destination()
        title = f'FrogBot Help - `{self.get_command_signature(group)}`'
        footer = f'An underlined command has sub-commands.\n' \
                 f'See {self.clean_prefix}help <command name> for more details on individual commands.'
        command_list = await self.filter_commands(group.commands, sort=True)
        out = generate_command_names(command_list, short_doc=True)

        source = HelpMenu(data=out, ctx=self.context, embed_title=title, embed_footer=footer)
        command_menu = menus.MenuPages(source=source, clear_reactions_after=True)
        await command_menu.start(self.context, channel=to_send)

    async def send_command_help(self, command):
        to_send = self.get_destination()
        embed = create_default_embed(self.context)
        embed.title = f'FrogBot Help - `{self.get_command_signature(command)}`'
        embed.description = command.help or 'No help specified.'
        embed.set_footer(text=f'An underlined command has subcommands.\n'
                              f'See {self.clean_prefix}help <command name> for more details '
                              f'on individual commands')
        await to_send.send(embed=embed)


class Help(commands.Cog, name='Help'):
    def __init__(self, bot):
        self._original_help_command = bot.help_command
        self.bot = bot
        bot.help_command = CustomHelp()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(Help(bot))
