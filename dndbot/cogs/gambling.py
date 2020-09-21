from discord.ext import commands
import discord
from utils.functions import create_default_embed
import datetime
from utils.objects import GamblingUser


class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.mdb['gambling']
        self.starting_money = 100
        # Set BEFORE to 1 month from startup for kits.
        self.BEFORE = datetime.datetime.now() - datetime.timedelta(days=30)

    def get_user_nx(self, user: discord.Member):
        """Returns user from database, creates user if user does not exist"""
        db = self.db
        data = db.find_one({'_id': user.id})
        if not data:
            data = {
                '_id': user.id,
                'money': self.starting_money,
                'last_daily_kit': self.BEFORE.strftime(GamblingUser.time_format())
            }
            db.insert_one(data)
        return GamblingUser(user=user,
                            money=data['money'],
                            last_daily_kit=datetime.datetime.strptime(data['last_daily_kit'],
                                                                      GamblingUser.time_format()))


def setup(bot):
    bot.add_cog(Gambling(bot))
