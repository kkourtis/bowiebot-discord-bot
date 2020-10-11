# owner.py

import discord
from discord.ext import commands
import asyncpg
import asyncio

import traceback
import re
import os

import config
from cogs.utils import db, paginator


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def plonk(self, ctx, user_id: int, *, u_reason: str = None):
        if u_reason is None:
            q = f"insert into plonks (user_id) VALUES ({user_id})"
        else:
            q = f"insert into plonks (user_id, reason) VALUES ({user_id}, '{u_reason}')"
        dupe_q = f"select user_id from plonks where user_id = {user_id}"
        async with self.bot.pool.acquire() as conn:
            check_v = await conn.fetchrow(dupe_q)
            if check_v is not None:
                await ctx.send(f'{user_id} has already been plonked')
                return
            await conn.execute(q)
            await ctx.message.add_reaction('\U00002705')

    @plonk.command(name='list')
    @commands.is_owner()
    async def list_plonks(self, ctx, user_id: int = None):
        """Lists users that are globally plonked"""
        await ctx.trigger_typing()
        if user_id is None:
            q = """select * from plonks where guild_id IS NULL"""
            values = await self.bot.pool.fetchrow(q)
            plonked = []
            for plonked_user in values:
                try:
                    user = self.bot.get_user(int(plonked_user['user_id']))
                    user_info = f"{user.id} | {user}"
                except:
                    user_info = f"{plonked_user['user_id']} | User Not Visible"

                plonked.append(user_info)

            if plonked == []:
                plonked.append('No users have been plonked')

            page = paginator.Pages(ctx, entries = tuple(plonked))
            page.embed.set_author(name='Users plonked')
            await page.paginate()
            return
        else:
            q = f"""select * from plonks where guild_id IS NULL and user_id = {user_id}"""
            value = await self.bot.pool.fetchrow(q)
            e = discord.Embed(color=discord.Color.gold())
            desc = '```Markdown\n'
            try:
                get_user = self.bot.get_user(user_id)
                desc += f'Name: {get_user}\n'
            except:
                desc += f'Name: User Not Visible\n'
            desc += f"ID: {value['user_id']}\n"
            desc += f"Reason: {value['reason']}\n"
            desc += f"Plonked on {value['date']}\n"
            desc += '```'
            e.description = desc

            await ctx.send(embed=e)
            return

    @commands.command()
    @commands.is_owner()
    async def unplonk(self, ctx, user_id: str):
        q = f"delete from plonks where user_id = {user_id} and guild_id IS NULL"
        await self.bot.pool.execute(q)
        await ctx.message.add_reaction('\U00002705')


    @commands.command(name='pc')
    @commands.is_owner()
    async def change_presence(self, ctx, *, game: str):
        game = discord.Game(name=game)
        await self.bot.change_presence(activity=game)
        await ctx.message.add_reaction('\U00002705')

    @commands.group()
    @commands.is_owner()
    async def icon(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        await ctx.send(self.bot.user.avatar_url)

    @icon.command()
    @commands.is_owner()
    async def change(self, ctx, url : str = None):
        import os
        import aiohttp
        from PIL import Image
        import io

        image = url or ctx.message.attachments[0].url

        async with aiohttp.ClientSession() as cs:
            async with cs.get(image) as r:
                data = await r.content.read()
                image = Image.open(io.BytesIO(data))
                img_name = (len(os.listdir('files/avatar')))
                image.save('files/avatar/{}.PNG'.format(img_name), 'PNG')
                with open('files/avatar/{}.PNG'.format(img_name), 'rb') as f:
                    await self.bot.user.edit(avatar=f.read())
        await ctx.message.add_reaction('\U00002705')

    @commands.command()
    @commands.is_owner()
    async def sql(self, ctx, *, query: str):
        values = await self.bot.pool.fetch(query)
        await ctx.send(values)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        else:
            return content

    def get_syntax_error(self, e):
        if e.text is None:
            return '```py\n{0.__class__.__name__}: {0}\n```'.format(e)
        return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(e, '^', type(e).__name__)

    @commands.command(name='eval', hidden=True)
    @commands.is_owner()
    async def _eval(self, ctx, *, body: str):
        """Shamefully copied from Rapptz's RoboDanny eval command since I don't know how to make one myself.
        Converted to work on REWRITE
        https://github.com/Rapptz/RoboDanny/blob/master/cogs/repl.py#L31-L75"""
        import traceback
        from contextlib import redirect_stdout
        import textwrap
        import io
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.message.channel,
            'author': ctx.message.author,
            'server': ctx.message.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = 'async def func():\n%s' % textwrap.indent(body, '  ')

        try:
            exec(to_compile, env)
        except SyntaxError as e:
            return await ctx.send(self.get_syntax_error(e))

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send('```py\n{}{}\n```'.format(value, traceback.format_exc()))
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send('```py\n%s\n```' % value)
            else:
                self._last_result = ret
                await ctx.send('```py\n%s%s\n```' % (value, ret))

    @commands.command()
    @commands.is_owner()
    async def pm(self, ctx, user: discord.User, *, content: str):
        """Sends a PM to a user via ID"""

        msg = '```'+content+'```' + '*This DM is not monitored. Contact ToastyGyro#8123.*'

        try:
            await user.send(msg)
        except:
            ctx.send('PM could not be sent', delete_after=10)
        else:
            await ctx.message.add_reaction('\U00002705')

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, name: str):
        """Loads a module"""
        try:
            self.bot.load_extension(name)
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.message.add_reaction('\U00002705')

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, name: str):
        """Unloads a module"""
        if 'Owner' in name or 'owner' in name:
            return
        try:
            self.bot.unload_extension(name)
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}```')
        else: 
            await ctx.message.add_reaction('\U00002705')

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, name: str):
        try:
            self.bot.reload_extension(name)
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}```')
        else: 
            await ctx.message.add_reaction('\U00002705')            

    @commands.command()
    @commands.is_owner()
    async def logout(self, ctx):
        """Quits the bot"""
        await self.bot.logout()

def setup(bot):
    bot.add_cog(Owner(bot))
