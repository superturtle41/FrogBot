import discord

CHANNEL_ADMIN = discord.PermissionOverwrite(
    read_messages=True,
    send_messages=True,
    manage_messages=True,
    manage_channels=True,
    read_message_history=True
)
CHANNEL_READ_WRITE = discord.PermissionOverwrite(
    read_messages=True,
    send_messages=True,
    read_message_history=True,
)
CHANNEL_HIDDEN = discord.PermissionOverwrite(
    read_messages=False,
    send_messages=False,
    read_message_history=False
)
CHANNEL_READ = discord.PermissionOverwrite(
    read_messages=True,
    send_messages=False,
    read_message_history=True
)