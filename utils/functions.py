import discord


async def try_delete(message):
    try:
        await message.delete()
    except discord.HTTPException:
        pass


def create_default_embed(bot, ctx) -> discord.Embed:
    embed = discord.Embed(color=discord.colour.Color.orange())
    embed.set_author(name=ctx.message.author.display_name, icon_url=str(ctx.message.author.avatar_url))
    embed.set_footer(text=bot.user.name, icon_url=str(bot.user.avatar_url))
    return embed


def auth_and_chan(ctx):
    """Message check: same author and channel"""

    def chk(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    return chk


def get_positivity(string):
    if isinstance(string, bool):  # oi!
        return string
    lowered = string.lower()
    if lowered in ('yes', 'y', 'true', 't', '1'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0'):
        return False
    else:
        return None
