# mod.py

import discord
from discord.ext import commands
import asyncio
import config
from cogs.utils import prefix, db, paginator
import re

class BlacklistedUser:
    def __init__(self, id, name, guild, reason, date_banned):
        self.id = id
        self.name = name
        self.guild = guild
        self.reason = reason
        self.date_banned = date_banned

    @classmethod
    async def convert(cls, ctx, arguement):
        try:
            user = await commands.UserConverter().convert(ctx, str(arguement))
        except:
            user = None

        if user is not None:
            user_id = user.id
        else:
            if re.search('[a-zA-Z]', str(arguement)):
                return
            user_id = arguement

        q = f"select * from plonks where user_id = '{user_id}' and guild_id = '{ctx.guild.id}'"
        db_user = await ctx.bot.pool.fetchrow(q)
        if db_user is None:
            return
        reason = db_user['reason']
        return cls(db_user['user_id'], db_user['name'], ctx.guild, reason, db_user['date'])


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._description = """Commands that are only available to users with specific permissions"""
        self._short_description = "\n".join(self._description.splitlines()[0:1])

    @commands.command(name='prefix')
    @commands.guild_only()
    async def _prefix(self, ctx, new_prefix = None):
        """View the prefixes used to invoke commands"""
        if ctx.invoked_subcommand is not None:
            return
        if new_prefix is None:
            prefixes = self.bot.command_prefix(self.bot, ctx.message)
            prefixes = set(prefixes)
            prefixes.discard(f'<@!{ctx.bot.user.id}> ')

            desc = f'{ctx.bot.user.mention}'
            for p in prefixes:
                if p is None:
                    continue
                if p == f'<@{ctx.bot.user.id}> ':
                    continue
                desc += f'or `{p}` '

            e = discord.Embed(title='Prefixes available on this server', description=desc, colour=discord.Color.gold())

            await ctx.send(embed=e)
        elif new_prefix is not None and commands.has_permissions(manage_guild=True):
            prefix.update(ctx.guild.id, new_prefix)
            await ctx.message.add_reaction('\U00002705')

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def clean(self, ctx, limit: int = 100):
        """Removes Bowie Bot messages from a channel"""
        server_prefixes = tuple(prefix.calculate(ctx.bot, ctx.message))

        def check(m):
            return m.author == ctx.me or m.content.startswith(server_prefixes)

        deleted = await ctx.channel.purge(limit=limit, check=check, before=ctx.message)
        if len(deleted) == 1:
            msg = 'message deleted'
        else:
            msg = 'messages deleted'
        await ctx.send(f'**{len(deleted)}** {msg}')

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx, user = None, *, reason: str = None):
        """Blocks a user from using Bowie Bot in the current server"""
        if ctx.invoked_subcommand is not None:
            return

        if user is None and reason is None:
            await self.display_blacklist(ctx)
            return

        if user is not None:
            try:
                user = await commands.UserConverter().convert(ctx, user)
                user_id = user.id
            except commands.BadArgument:
                if re.search('[a-zA-Z]', user):
                    print(user, 'Failed')
                    return
                else:
                    user_id = user
            
        if user_id == ctx.guild.owner_id:
            await ctx.send('The owner of the server cannot be blacklisted', delete_after=15)

        check_for_dupe = f"select user_id from plonks where user_id = '{user_id}' and guild_id = '{ctx.guild.id}'"
        dupe_result = await self.bot.pool.fetchrow(check_for_dupe)
        if dupe_result is not None:
            await self.display_blacklist(ctx, user)
            return
        if reason is None:
            q = f"insert into plonks (user_id, name, guild_id) VALUES ({user_id}, $1, {ctx.guild.id})"
            await self.bot.pool.execute(q, user.name)
        else:
            q = f"insert into plonks (user_id, name, guild_id, reason) VALUES ({user_id}, $1 , {ctx.guild.id}, $2)"
            await self.bot.pool.execute(q, user.name, reason)
        await ctx.message.add_reaction('\U00002705')

    async def display_blacklist(self, ctx, user: discord.User = None):
        """Shows list of blacklisted users in a server"""
    
        await ctx.trigger_typing()
        if user is None:
            q = f"""select * from plonks where guild_id = '{ctx.guild.id}'"""
            values = await self.bot.pool.fetch(q)

            banned = []
            for banned_user in values:
                try:
                    user = self.bot.get_user(int(banned_user['user_id']))
                    user_info = f"{user.id} | {user}"
                except:
                    user_info = f"User Not Found | {int(banned_user['user_id'])}"

                banned.append(user_info)
            
            if banned == []:
                banned.append("No users blacklisted on this server")

            page = paginator.Pages(ctx, entries=tuple(banned))
            page.embed.set_author(name="Users blacklisted from Bowie Bot")

            await page.paginate()

        else:
            user = await BlacklistedUser.convert(ctx, user)
            q = f"select * from plonks where user_id = '{user.id}' and guild_id = '{ctx.guild.id}'"
            db_user = await self.bot.pool.fetchrow(q)
            e = discord.Embed(color=discord.Color.gold())
            desc = '```markdown\n'
            desc += f"Name: {db_user['name']}\n"
            desc += f"ID: {db_user['user_id']}\n"
            desc += f"Reason: {db_user['reason']}\n"
            desc += f"Blacklisted on {db_user['date']}"
            desc += '```'
            e.description=desc

            await ctx.send(embed=e)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def unblacklist(self, ctx, *, user: BlacklistedUser):
        """Removes a user from this servers blacklist.

        Only users with administrator permissions can use this command."""

        q = f"delete from plonks where user_id = '{user.id}' and guild_id = '{ctx.guild.id}'"
        await self.bot.pool.execute(q)
        await ctx.message.add_reaction('\U00002705')

    async def get_blacklisted_user(self, ctx, user_id):
        pass

def setup(bot):
    bot.add_cog(Mod(bot))