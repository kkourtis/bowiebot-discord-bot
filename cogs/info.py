# info.py

import discord
import asyncio
from discord.ext import commands
import datetime
import time
import psutil

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._process = psutil.Process()

        self._description = """Get information on the bot, users, and the server"""
        self._short_description = "\n".join(self._description.splitlines()[0:1])
    
    @commands.group()
    async def info(self,ctx):
        """Get info on the bot"""
        if ctx.invoked_subcommand is not None:
            return
        if len(ctx.message.content.split()) > 1:
            return

        appinfo = await self.bot.application_info()
        mem_usage = self._process.memory_full_info().uss / 1024 ** 2
        cpu_usage = self._process.cpu_percent() / psutil.cpu_count()

        e = discord.Embed(description=appinfo.description, colour=discord.Colour.gold())
        e.set_thumbnail(url=self.bot.user.avatar_url)
        e.add_field(name='ID', value=appinfo.id)
        e.add_field(name='Library', value=f"discord.py {discord.__version__}")
        e.add_field(name='Users Visible', value=str(len(self.bot.users)))
        e.add_field(name='Guilds Visible', value=str(len(self.bot.guilds)))
        e.add_field(name='CPU Usage', value=f'{cpu_usage:.2f}%')
        e.add_field(name='RAM Usage', value=f'{mem_usage:.2f}MB')
        e.add_field(name='Uptime', value=self.get_uptime())
        e.add_field(name='Owner', value=appinfo.owner)

        await ctx.send(embed=e)

    @info.command(aliases=['member'])
    async def user(self, ctx, *, user: discord.Member = None):
        """Get info on a user"""

        await ctx.trigger_typing()

        user = user or ctx.author
        em = discord.Embed(colour=discord.Colour.gold())
        em.timestamp = datetime.datetime.now()
        em.set_thumbnail(url=user.avatar_url)
        em.set_author(name=user.name, icon_url=user.avatar_url)
        if user.nick is not None:
            em.add_field(name='Nickname', value=user.nick)
        em.add_field(name='ID', value=user.id)
        em.add_field(name='Status', value=user.status)
        em.add_field(name='Account Created On', value=user.created_at.strftime('%A, %B %d %Y at %I:%M:%S %p'),
                     inline=False)
        em.add_field(name='Joined Server On', value=user.joined_at.strftime('%A, %B %d %Y at %I:%M:%S %p'))
        roles = ''
        for role in user.roles:
            if role.name == '@everyone':
                continue
            elif roles == '':
                roles += f'{role.name}'
            else:
                roles += f', {role.name}'
        em.add_field(name='Roles on this Server', value=roles, inline=False)
        await ctx.send(embed=em)

    @info.command(aliases=['guild'])
    @commands.guild_only()
    async def server(self, ctx):
        """Get info on a guild"""
        with ctx.typing():
            guild = ctx.guild
            em = discord.Embed(colour=discord.Colour.gold())
            em.timestamp = datetime.datetime.now()
            em.set_thumbnail(url=ctx.guild.icon_url)
            em.set_author(name=guild.name, icon_url=ctx.guild.icon_url)
            em.add_field(name='ID', value=guild.id)
            online_count = 0
            for i in guild.members:
                if str(i.status) != 'offline':
                    online_count += 1
            em.add_field(name='Members', value=f'{len(guild.members)} ({online_count} online)')
            em.add_field(name='Region', value=guild.region)
            em.add_field(name='Owner', value=guild.owner)
            em.add_field(name='Text Channels', value=str(len(guild.text_channels)))
            em.add_field(name='Voice Channels', value=str(len(guild.voice_channels)))
            em.add_field(name='Guild Created On', value=guild.created_at.strftime('%A, %B %d %Y at %I:%M:%S %p'))
            await ctx.send(embed=em)

    @info.command()
    @commands.guild_only()
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """Get info on a channel"""
        with ctx.typing():
            channel = channel or ctx.channel
            em = discord.Embed(colour=discord.Colour.gold())
            em.timestamp = datetime.datetime.now()
            em.set_author(name=channel.name, icon_url=ctx.guild.icon_url)
            em.add_field(name='ID', value=channel.id)
            em.add_field(name='Channel Created On', value=channel.created_at.strftime('%A, %B %d %Y at %I:%M:%S %p'))
            await ctx.send(embed=em)

    @commands.command()
    async def avatar(self, ctx, *, user: discord.Member = None):
        """Posts the avatar of a user"""
        user = user or ctx.author
        avi = user.avatar_url
        e = discord.Embed()
        e.set_author(name=user.name)
        e.set_image(url=avi)
        await ctx.send(embed=e)

    @commands.command()
    async def uptime(self, ctx):
        """Get the bots uptime"""
        await ctx.send(self.get_uptime())


    def get_uptime(self):
        """Returns the bots uptime as a str"""
        total_seconds = time.time() - self.bot.uptime

        days = total_seconds // 86400
        secs_days = total_seconds % 86400

        hours = secs_days // 3600
        secs_hours = secs_days % 3600

        minutes = secs_hours // 60
        secs_minutes = secs_hours % 60

        seconds = secs_minutes

        uptime = ''

        if int(days) == 1:
            uptime += f'{int(days)}d, '
        elif int(days) > 0:
            uptime += '{}d, '.format(int(days))
        if int(hours) > 0:
            uptime += '{}h, '.format(int(hours))
        elif int(days) > 0:
            uptime += '{}hs, '.format(int(hours))
        if int(minutes) > 0:
            uptime += '{}m, '.format(int(minutes))
        elif int(hours) > 0:
            uptime += '{}m, '.format(int(minutes))
        if int(seconds) == 1:
            uptime += '{}s'.format(int(seconds))
        else:
            uptime += '{}s'.format(int(seconds))
        return uptime


def setup(bot):
    bot.add_cog(Info(bot))
