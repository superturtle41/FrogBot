import discord
from discord.ext import commands

from utils.constants import DMS
from utils.functions import create_default_embed, try_delete, get_positivity


class QuestRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='questrole', description='Creates a role for quests')
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_any_role(*DMS)
    async def create_quest_role(self, ctx):
        """
        Creates a Role for Quests

        The role created will have the default permissions that \@everyone has at the time of creation.
        """
        author = ctx.author
        channel = ctx.channel
        user_mention = discord.AllowedMentions(users=[ctx.author])

        color_converter = commands.ColorConverter()

        def chk(m):
            return m.author == author and m.channel == channel

        async def prompt(message: discord.Message, ebd: discord.Embed, content: str,
                         mentions: discord.AllowedMentions = None):
            if content:
                ebd.description = content
            await message.edit(embed=ebd, allowed_mentions=mentions)
            result = await self.bot.wait_for('message', check=chk, timeout=60)
            if result is None:
                return result
            content = result.content
            await try_delete(result)
            return content, ebd

        def check_stop(content):
            if content.lower() in ['stop', 'cancel', 'quit', 'exit']:
                return True
            else:
                return False

        async def stop(question_msg):
            await try_delete(question_msg)
            await ctx.send('Operation Cancelled, stopping.', delete_after=10)

        embed = create_default_embed(ctx)
        embed.title = 'Quest Role Creation'
        question_msg = await ctx.send(embed=embed)
        role_name, embed = await prompt(question_msg, embed,
                                        f'{ctx.author.mention}, what would you like this role to be called?',
                                        mentions=user_mention)
        if check_stop(role_name):
            return await stop(question_msg)

        role_color, embed = await prompt(question_msg, embed,
                                         f'Role Name: `{role_name}`\nWhat color would you like this role to be?')
        if check_stop(role_color):
            return await stop(question_msg)
        try:
            color = await color_converter.convert(ctx=ctx, argument=role_color.lower())
        except (commands.CommandError, commands.BadColourArgument):
            await try_delete(question_msg)
            return await ctx.send('Invalid Color provided, exiting.', delete_after=10)

        embed.color = color

        confirm_content, embed = await prompt(question_msg, embed,
                                              f'Role `{role_name}` with the color of this embed '
                                              f'will be created. Please confirm.')
        if get_positivity(confirm_content):
            new_role = await ctx.guild.create_role(name=role_name, color=color, reason='Quest Role Creation')
            await ctx.send(f'Role {new_role.mention} created.', delete_after=10,
                           allowed_mentions=discord.AllowedMentions(roles=[new_role]))
            return await try_delete(question_msg)
        else:
            return await stop(question_msg)


def setup(bot):
    bot.add_cog(QuestRoles(bot))
