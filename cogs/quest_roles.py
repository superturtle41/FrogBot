from discord.ext import commands
import asyncio
import discord
from utils.functions import create_default_embed, try_delete, get_positivity


class QuestRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='questrole', description='Creates a role for quests')
    async def create_quest_role(self, ctx):
        """
        Creates a Role for Quests

        The role created will have the default permissions that \@everyone has
        """
        author = ctx.author
        channel = ctx.channel
        user_mention = discord.AllowedMentions(users=[ctx.author])

        def chk(m):
            return m.author == author and m.channel == channel

        async def get_response(timeout=90):
            try:
                response = await self.bot.wait_for('message', timeout=timeout, check=chk)
                return response
            except asyncio.TimeoutError:
                await ctx.send('Timed out waiting for answer.')
                return -1

        async def next_question(ebd, qmsg, newdesc, mentions=None):
            ebd.description = newdesc
            await qmsg.edit(embed=ebd, allowed_mentions=mentions)
            msg = await get_response(timeout=60)
            content = msg.content
            await try_delete(msg)
            return content

        def check_stop(content):
            if content.lower() == 'stop' or content.lower() == 'cancel':
                return True
            else:
                return False

        embed = create_default_embed(ctx)
        embed.title = 'Quest Role Creation'
        question_msg = await ctx.send(embed=embed)
        role_name = await next_question(embed, question_msg, f'{ctx.author.mention}, '
                                                             f'what would you like this role to be called?',
                                        user_mention)
        if check_stop(role_name):
            return
        role_color = await next_question(embed, question_msg, f'Role Name: `{role_name}`\n'
                                                              f'What color would you like this role to be?')
        if check_stop(role_color):
            return
        try:
            color_hex = int(role_color, 16)
            color = discord.Color(color_hex)
        except ValueError:
            await try_delete(question_msg)
            return await ctx.send('Invalid Hex Code, exiting.', delete_after=10)
        embed.color = color
        confirm_content = await next_question(embed, question_msg, f'Role `{role_name}` with the color of this embed'
                                                                   f' will be created. Please confirm.')
        if get_positivity(confirm_content):
            new_role = await ctx.guild.create_role(name=role_name, color=color, reason='Quest Role Creation')
            await ctx.send(f'Role {new_role.mention} created.', delete_after=10,
                           allowed_mentions=discord.AllowedMentions(roles=[new_role]))
            await try_delete(question_msg)
        else:
            await ctx.send('Operation Cancelled, stopping.')


def setup(bot):
    bot.add_cog(QuestRoles(bot))
