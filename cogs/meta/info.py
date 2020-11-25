import discord
from discord.ext import commands

from utils.constants import STATUS_EMOJIS, STATUS_NAMES, BADGE_EMOJIS, SUPPORT_SERVER_ID, DATE_FORMAT
from utils.functions import create_default_embed, member_in_guild


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='servinfo', aliases=['sinfo'])
    @commands.guild_only()
    async def server_info(self, ctx):
        """
        Displays information about the current server.
        """
        embed = create_default_embed(ctx)
        guild = ctx.guild
        embed.title = f'{guild.name} - Server Information'
        general_info = f'**ID:** {guild.id}\n' \
                       f'**Owner:** {guild.owner.mention}\n' \
                       f'Created: {guild.created_at.strftime(DATE_FORMAT)}'
        embed.add_field(name='General Info', value=general_info, inline=False)
        emoji_x = 0
        emojis = []
        for emoji in guild.emojis:
            emoji_x += 1
            if emoji_x >= 10:
                break
            emojis.append(emoji)
        emoji_info = f'{len(guild.emojis)} emoji{"s" if len(guild.emojis) != 1 else ""}\n' \
                     f'{",".join([str(e) for e in emojis])} {"..." if emoji_x >= 10 else ""}'
        embed.add_field(name='Emojis', value=emoji_info, inline=False)
        bots = [member for member in guild.members if member.bot]
        member_stats = f'{guild.member_count - len(bots)} members ({len(bots)} bots)'
        embed.add_field(name='Member Info', value=member_stats)
        channels = f'{len([c for c in guild.categories])} categories, ' \
                   f'{len([c for c in guild.channels if isinstance(c, discord.TextChannel)])} text channels, ' \
                   f'{len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])} voice channels.'
        embed.add_field(name='Channel Info', value=channels)
        embed.set_thumbnail(url=str(guild.icon_url))

        return await ctx.send(embed=embed, allowed_mentions=None)

    @commands.command(name='memberinfo', aliases=['minfo'])
    @commands.guild_only()
    async def member_info(self, ctx, who: discord.Member = None):
        """
        Shows information about a member in this server.
        """
        if who is None:
            who = ctx.author
        embed = create_default_embed(ctx)
        badges = ''
        if who.id == self.bot.owner:
            badges += f'{BADGE_EMOJIS["bot_owner"]} '
        if who.id == ctx.guild.owner.id:
            badges += f'{BADGE_EMOJIS["server_owner"]} '
        support_server = self.bot.get_guild(SUPPORT_SERVER_ID)
        if support_server is not None and member_in_guild(who.id, support_server):
            badges += f'{BADGE_EMOJIS["support_server"]}'

        embed.title = f'Member Information - {who.display_name} {badges}'

        # -- Basics --
        embed.add_field(name='Name', value=f'{who.mention}')
        embed.add_field(name='Username', value=f'{who.name}#{who.discriminator}')
        embed.add_field(name='ID', value=f'{who.id}')
        embed.add_field(name='Status', value=f'Status: {STATUS_EMOJIS[str(who.status)]}'
                                             f' ({STATUS_NAMES[str(who.status)]})')

        # -- Roles --
        embed.add_field(name='Roles', value=f'{len(who.roles)} role(s)')
        embed.add_field(name='Top Role',
                        value=f'{who.top_role.mention if who.top_role.name != "@everyone" else "Default Role"}'
                              f' (Position {who.top_role.position}/{ctx.guild.roles[-1].position})')
        embed.add_field(name='Is Server Owner', value=f'{"True" if ctx.guild.owner.id == who.id else "False"}')

        # -- Date Information --
        embed.add_field(name='Account Created At', value=who.created_at.strftime(DATE_FORMAT))
        embed.add_field(name='Joined Server At', value=who.joined_at.strftime(DATE_FORMAT))

        embed.set_thumbnail(url=who.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(name='avatar')
    async def avatar(self, ctx, who: discord.Member = None):
        """
        Gives you the avatar of whoever you specify, or yourself if you don't specify anyone.
        """
        embed = create_default_embed(ctx)
        if not who:
            who = ctx.author
        embed.title = f'Avatar for {who.display_name}'
        embed.set_image(url=str(who.avatar_url_as(format='png')))
        return await ctx.send(embed=embed)

    @commands.command(name='emoji')
    async def emoji_info(self, ctx, emoji_to_parse: discord.Emoji):
        """
        Returns custom emoji information.
        """
        embed = create_default_embed(ctx)
        embed.title = f'Emoji - :{emoji_to_parse.name}:'

        embed.add_field(name='Guild', value=emoji_to_parse.guild.name)
        embed.add_field(name='ID', value=emoji_to_parse.guild.id)

        embed.set_image(url=str(emoji_to_parse.url))

        await ctx.send(embed=embed)

    @commands.command(name='permissions', aliases=['perms'])
    @commands.guild_only()
    async def show_perms(self, ctx, who: discord.Member = None):
        """
        Shows the permissions for the user specified in the current channel.
        Will show permissions for yourself if nobody is specified.
        """
        if who is None:
            who = ctx.author
        embed = create_default_embed(ctx)
        embed.title = f'Permissions for {who.display_name}'
        yes, no = "\U00002705", "\U0001f6ab"
        out = ''
        for perm, value in who.permissions_in(ctx.channel):
            out += f'{yes if value else no} | {perm.replace("_", " ").title()}\n'
        embed.description = out

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
