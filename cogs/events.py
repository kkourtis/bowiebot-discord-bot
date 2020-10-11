# events.py

import discord
from discord.ext import commands
from cogs.utils import prefix, db
import config
import os

class Events(commands.Cog):
    """This class handles code that
    needs to execute at the time 
    the bot joins a guild"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Insert the guild into the databases
        prefix.insert(guild.id, config.PREFIX)
        async with self.bot.pool.acquire() as conn:
            await db.insert_guild(guild.id, conn)
        # Here add a custom sound folder for them
        path = f'files/custom_sound/{guild.id}'
        if not os.path.exists(path):
            os.mkdir(path)
            

    @commands.Cog.listener()
    async def on_guild_remove(self,guild):
        # Do nothing, imma keep all that juicy data like, their prefix
        return

def setup(bot):
    bot.add_cog(Events(bot))

