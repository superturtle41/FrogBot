import discord


async def try_delete(message):
    try:
        await message.delete()
    except discord.HTTPException:
        pass
