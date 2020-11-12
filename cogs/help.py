from discord.ext import commands, menus
from utils.functions import create_default_embed
import discord


class HelpCogMenu(menus.ListPageSource):
    def __init__(self, data, ctx, embed_title, embed_footer, embed_desc):
        super().__init__(data, per_page=10)
        self.context = ctx
        self.embed_title = embed_title
        self.embed_footer = embed_footer
        self.embed_desc = embed_desc

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = create_default_embed(self.context)
        embed.title = self.embed_title
        embed.description = self.embed_desc
        embed.set_footer(text=self.embed_footer)
        message = '\n'.join([command for _, command in enumerate(entries, start=offset)])
        message = message + f'\n\nPage {menu.current_page+1}/{self.get_max_pages()}'
        embed.add_field(name='Commands', value=message)
        return embed


class HelpBotMenu(menus.ListPageSource):
    def __init__(self, data, ctx, embed_title, embed_footer, embed_desc):
        super().__init__(data, per_page=4)
        self.context = ctx
        self.embed_title = embed_title
        self.embed_footer = embed_footer
        self.embed_desc = embed_desc

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = create_default_embed(self.context)
        embed.title = self.embed_title
        embed.description = self.embed_desc
        # Entries = List[tuple(Cog, Commands)]
        for _, item in enumerate(entries, start=offset):
            command_list = generate_command_names(item[1], short_doc=True)
            embed.add_field(name=item[0].qualified_name, value='\n'.join(command_list), inline=False)
        embed.set_footer(text=f'Page {menu.current_page+1}/{self.get_max_pages()}\n'+self.embed_footer)
        return embed


def generate_command_names(command_list, short_doc=False):
    out = []
    for command in command_list:
        parent = (command.full_parent_name + " ") if command.full_parent_name else ""
        name = f'`{parent}{command.name}`'
        if isinstance(command, commands.Group) and len(command.commands):
            name = '__' + name + '__'
        if short_doc:
            name += f' - {command.short_doc}'
        out.append(name)
    return out


class CustomHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        to_send = self.get_destination()
        title = 'FrogBot Help'
        description = self.cog.bot.description
        footer = f'An underlined command has sub-commands.\n' \
                 f'See {self.clean_prefix}help <command name> for more details on individual commands.'
        filtered_mapping = []
        for cog in mapping:
            command_list = await self.filter_commands(mapping[cog], sort=True)
            if len(command_list) <= 0:
                continue
            filtered_mapping.append((cog, command_list))

        source = HelpBotMenu(data=filtered_mapping, ctx=self.context, embed_title=title, embed_footer=footer,
                             embed_desc=description or 'No description specified.')
        command_menu = menus.MenuPages(source=source, clear_reactions_after=True)
        await command_menu.start(self.context, channel=to_send)

    async def send_cog_help(self, cog):
        to_send = self.get_destination()
        embed = create_default_embed(self.context)
        title = f'FrogBot Help - `{cog.qualified_name}`'.strip()
        footer = f'An underlined command has sub-commands.\n' \
                 f'See {self.clean_prefix}help <command name> for more details on individual commands.'
        command_list = await self.filter_commands(cog.get_commands(), sort=True)
        embed.description = cog.description or 'No description specified.'
        out = generate_command_names(command_list)

        source = HelpCogMenu(data=out, ctx=self.context, embed_title=title, embed_footer=footer,
                             embed_desc=cog.description or 'No description specified.')
        command_menu = menus.MenuPages(source=source, clear_reactions_after=True)
        await command_menu.start(self.context, channel=to_send)

    async def send_group_help(self, group):
        to_send = self.get_destination()
        title = f'FrogBot Help - `{self.get_command_signature(group)}`'.strip()
        footer = f'An underlined command has sub-commands.\n' \
                 f'See {self.clean_prefix}help <command name> for more details on individual commands.'
        command_list = await self.filter_commands(group.commands, sort=True)
        out = generate_command_names(command_list, short_doc=True)

        source = HelpCogMenu(data=out, ctx=self.context, embed_title=title, embed_footer=footer,
                             embed_desc=group.description or 'No description specified.')
        command_menu = menus.MenuPages(source=source, clear_reactions_after=True)
        await command_menu.start(self.context, channel=to_send)

    async def send_command_help(self, command):
        to_send = self.get_destination()
        embed = create_default_embed(self.context)
        embed.title = f'FrogBot Help - `{self.get_command_signature(command).strip()}`'
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
