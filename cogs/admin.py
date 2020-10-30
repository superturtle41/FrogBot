from discord.ext import commands
from utils.checks import is_owner, is_authorized
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

    @commands.command(name='change_status', description='Owner Only - Changes the bot\'s status.', hidden=True)
    @is_owner()
    async def change_status(self, ctx, *, value: str):
        activity = discord.Game(name=f'{value} | {ctx.bot.prefix}help')
        await ctx.bot.change_presence(activity=activity)

        ctx.bot.mdb['bot_settings'].update_one({'setting': 'status'}, {'$set': {'status': value}}, upsert=True)

        return await ctx.send(f'Status changed to {value}')

    @commands.command(name='authorize', description='Add user to authorized list.', hidden=True)
    @is_authorized()
    async def authorize_add(self, ctx, to_auth: discord.Member):
        uid = ctx.author.id
        ctx.bot.mdb['authorized'].update_one({'_id': uid}, {'$set': {'_id': uid}}, upsert=True)

        return await ctx.send(f'User {ctx.author.display_name} added to authorized list.')

    @commands.command(name='ban', description='Bans a user from the server.')
    @is_owner()
    @commands.guild_only()
    async def manual_ban(self, ctx, to_ban: discord.Member, hard: bool = False):
        try:
            if hard:
                await ctx.guild.kick(to_ban)
            await ctx.guild.ban(to_ban, reason=f'Banned by {ctx.author.display_name}')
            await ctx.send(f'User `{to_ban.name}#{to_ban.discriminator}` has been banned from the server.')
        except discord.Forbidden:
            return await ctx.author.dm_channel.send('I do not have permissions to ban this user.')
        except discord.HTTPException:
            return await ctx.author.dm_channel.send('An unknown discord error occurred. Pleas try again later.')

    @commands.command(name='mute', description='Mutes a user. Prevents them from using the bot.', hidden=True)
    @is_authorized()
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
    @is_authorized()
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
