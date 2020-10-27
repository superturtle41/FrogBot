from discord.ext import commands
from utils.checks import is_owner
import discord


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stop", description="Owner Only - Stops Bot", hidden=True)
    @is_owner()
    async def stop(self, ctx, really: str = "no"):
        await ctx.send("Okay, shutting down...")
        if really == 'please':
            await ctx.send('Shutdown complete.')
            exit(0)
        else:
            await ctx.send('Invalid Control Sequence detected. Operation Aborted.')

    @commands.command(name='ban', description='Bans a user from the server.')
    @is_owner()
    @commands.guild_only()
    async def soft_ban(self, ctx, to_ban: discord.Member, *, reason: str = 'No Reason Specified.'):
        try:
            await ctx.guild.ban(to_ban, reason=f'{reason}\nBanned by {ctx.author.display_name}')
            await ctx.send(f'User `{to_ban.name}#{to_ban.discriminator}` has been banned from the server.')
        except discord.Forbidden:
            return await ctx.send('I do not have permissions to ban this user.')
        except discord.HTTPException:
            return await ctx.send('An unknown discord error occurred. Pleas try again later.')

    @commands.command(name='hardban', description='Bans a user from the server.', hidden=True)
    @is_owner()
    @commands.guild_only()
    async def hard_ban(self, ctx, to_ban: discord.Member, *, reason: str = 'No Reason Specified.'):
        try:
            await ctx.guild.kick(to_ban)
            await ctx.guild.ban(to_ban, reason=f'{reason}\nBanned by {ctx.author.display_name}')
            await ctx.author.dm_channel.send(f'User `{to_ban.name}#{to_ban.discriminator}` '
                                             f'has been banned from the server.')
        except (discord.Forbidden, discord.HTTPException):
            return

    @commands.command(name='mute', description='Mutes a user. Prevents them from using the bot.', hidden=True)
    async def mute(self, ctx, to_mute: discord.Member):
        record = {'_id': to_mute.id}
        db = self.bot.mdb['muted_clients']
        if db.find(record).count() == 0:
            db.insert_one(record)
            return await ctx.send(f'User {to_mute.name}#{to_mute.discriminator} has been muted.')
            self._update_muted()
        else:
            return await ctx.send(f'User {to_mute.name}#{to_mute.discriminator} has already been muted.')

    @commands.command(name='unmute', description='Un-mutes a user.', hidden=True)
    async def unmute(self, ctx, to_mute: discord.Member):
        record = {'_id': to_mute.id}
        db = self.bot.mdb['muted_clients']
        if db.find(record).count() != 0:
            db.delete_one(record)
            return await ctx.send(f'User {to_mute.name}#{to_mute.discriminator} has been unmuted.')
            self._update_muted()
        else:
            return await ctx.send(f'User {to_mute.name}#{to_mute.discriminator} is not muted.')

    def _update_muted(self):
        muted = []
        for muted_user in self.bot.mdb['muted_clients'].find({}):
            muted.append(muted_user['_id'])
        self.bot.muted = muted


def setup(bot):
    bot.add_cog(Admin(bot))
