import discord

DEV_ID = 175386962364989440
DM_CATEGORY_PERMS = discord.PermissionOverwrite(
    read_messages=True,
    send_messages=True,
    manage_messages=True,
    manage_channels=True,
    read_message_history=True
)
DM_ALLOWED_PERMS = discord.PermissionOverwrite(
    read_messages=True,
    send_messages=True,
    read_message_history=True,
)
OTHER_CATEGORY_PERMS = discord.PermissionOverwrite(
    read_messages=False,
    send_messages=False,
    read_message_history=False
)
ARCHIVED_PERMS = discord.PermissionOverwrite(
    read_messages=True,
    send_messages=False,
    read_message_history=True
)