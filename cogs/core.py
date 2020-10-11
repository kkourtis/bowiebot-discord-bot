# core.py

import discord
from discord.ext import commands
import asyncio
import time
import os

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._feedback_channel = self.bot.get_channel(347055340115853312)
        self._description = f"""General purpose commands"""
        self._short_description = "\n".join(self._description.splitlines()[0:1])
        
    @commands.group(name='quote', invoke_without_command=True)
    async def quote_post(self, ctx, message_id: int):
        """Reposts a previous message in the current channel. 
        Useful for bringing up a previous conversation"""

        if ctx.invoked_subcommand is not None:
            return

        msg = await ctx.channel.fetch_message(message_id)

        e = discord.Embed(colour=discord.Colour.gold(), timestamp=msg.created_at)
        e.set_author(name=msg.author, icon_url=msg.author.avatar_url)
        e.description = msg.content

        if len(msg.attachments) > 0:
            e.description += '\n\nAttachments:\n'
            for i in msg.attachments:
                e.description += f'{i.url}\n'
        
        await ctx.send(embed=e)

    @quote_post.command(name='from')
    async def quote_from(self, ctx, channel: discord.TextChannel, message_id: int):
        """Reposts a previous message from a different channel into the current one"""

        channel = channel or ctx.channel
        msg = await channel.fetch_message(message_id)

        e = discord.Embed(colour=discord.Colour.gold(), timestamp=msg.created_at)
        e.set_author(name=msg.author, icon_url=msg.author.avatar_url)

        e.description = msg.content

        if len(msg.attachments) > 0:
            e.description += '\n\nAttachments:\n'
            for i in msg.attachments:
                e.description += f'{i.url}\n'

        e.set_footer(text=f'Originally posted in {msg.channel}')

        await ctx.send(embed=e)

    @commands.command()
    async def invite(self, ctx):
        """Posts the OAuth 2 link to invite the bot to a server"""
        description = f'https://discordapp.com/oauth2/authorize?client_id=182753440722714624&scope=bot&permissions={self.bot.requested_permissions}'
        await ctx.send(embed=discord.Embed(title='Bowie Bot Invite Link',
                                        description=description, colour=discord.Colour.gold()))

    @commands.command(aliases=['latency'])
    async def ping(self, ctx):
        """View the reaction time of the bot"""
        a1 = time.time()
        api_ping = self.bot.latency * 1000
        b1 = time.time()
        rtt_in_ms = round(b1 - a1, 3)
        await ctx.send(f'Receive: {api_ping:.0f}ms, Reply: {rtt_in_ms*1000:.0f}ms')

#    @commands.group(name='help')
#    async def help_command(self, ctx, *, command: str = None):
#        """Displays help text for a command"""

def setup(bot):
    bot.add_cog(Core(bot))

def teardown(bot):
    return