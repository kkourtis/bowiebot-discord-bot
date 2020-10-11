# Bowie Bot Clean Up
# This project focuses on updating the bot to v1.0 of d.py rewrite
# as well as removing unneeded features and fixing other outstanding bugs
# Timestamp: 4/10/2019

import discord
from discord.ext import commands
import asyncio
import time
from cogs.utils import prefix, db
import config
import aiohttp
import os

bot_description = "A bot focusing on playing sound clips in a voice channel"

extensions = {
    'cogs.core',
    'cogs.events',
    'cogs.info',
    'cogs.mod',
    'cogs.images',
    'cogs.owner',
    'cogs.sound'
}

def _prefix_callable(bot,msg):
    return prefix.calculate(bot,msg)

class BowieBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=_prefix_callable, description=bot_description,owner_id=config.OWNERID)
        #self.remove_command('help')
        self.support_invite = config.HOME_SERVER_INVITE_URL
        self.requested_permissions = config.REQUESTED_PERMISSIONS
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.default_prefix = config.PREFIX

        for ext in extensions:
            try:
                self.load_extension(ext)
            except Exception as e:
                print(f'Failed to load extension {ext}.')
                print(e)

    async def on_ready(self):
        if not hasattr(self,'uptime'):
            self.uptime = time.time()

        if not hasattr(self,'invite'):
            self.invite = discord.utils.oauth_url(self.user.id)

        self.connection = await db.connect()
        self.pool = await db.create_pool(config.DB)

        db_check_start = time.time()
        print('Checking databases for missing guilds')
        prefix.add_missing_guilds(self.guilds)
        async with self.pool.acquire() as conn:
            await db.add_missing_guilds(self.guilds, conn)
        added_cs_folder = 0
        for guild in self.guilds:
            cs_path = f'files/custom_sound/{guild.id}'
            if not os.path.exists(cs_path):
                os.mkdir(cs_path)
                added_cs_folder += 1
        print(f'{added_cs_folder} guilds added to custom sounds')
        print('Database Check Complete')
        print(f'Time elapsed: {time.time()-db_check_start}')

        bot_status = discord.Game(name='Use bb$help')
        await self.change_presence(activity=bot_status)

        print()
        print('-------')
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('-------')
        print()

    async def on_message(self, message):

        """Ignores messages from all bot accounts"""
        if message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        # Check if the user invoking a command is plonked, globally or locally
        if message.guild is None:
            # If message is sent in a DM, only check for global plonk
            q = f"select user_id from plonks where user_id = '{message.author.id}' and guild_id IS NULL"
        else:
            q = f"select user_id, guild_id from plonks where " \
                f"user_id = '{message.author.id}' and guild_id = '{message.guild.id}'" \
                f"or user_id = '{message.author.id}' and guild_id IS NULL"
        async with self.pool.acquire() as conn:
            value = await conn.fetchrow(q)

        try:
            if value['guild_id'] == str(message.guild.id) or value['guild_id'] is None:
                return
        except:
            pass

        await self.invoke(ctx)

bot = BowieBot()
bot.run(config.TOKEN, reconnect=True)