import discord
from discord.ext import commands
import asyncio

import os
import random
import re

from PIL import Image, ImageOps
import io

from cogs.utils import prefix, db, paginator


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._link_check = re.compile(r"(?:https|http)?:\/\/.*\.(?:png|jpg|gif|gifv|webm)")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.content == '':
            return

        content = await prefix.remove_prefix_from_message(self.bot, message)
        if content is None:
            return

        if content not in os.listdir(f'files/images/commands'):
            return

        """Check if the user is plonked"""
        q = f"select user_id, guild_id from plonks where " \
            f"user_id = '{message.author.id}' and guild_id = '{message.guild.id}'" \
            f"or user_id = '{message.author.id}' and guild_id IS NULL"
        value = await self.bot.connection.fetchrow(q)
        try:
            if value['guild_id'] == str(message.guild.id) or value['guild_id'] is None:
                return
        except:
            pass

        await self.post_image(content, message.channel)

    async def post_image(self, command, channel):
        with channel.typing():
            folder = os.listdir(f'files/images/commands/{command}')
            choice = random.choice(folder)
            print(choice)
            file_location = f'files/images/commands/{command}/{choice}'
            with open(file_location, 'rb') as f:
                upload_file = discord.File(f)
                await channel.send(file=upload_file)

    @commands.command(hidden=True)
    async def beautiful(self, ctx, *, user: discord.Member=None):
        """Now that... that is beautiful

        Accepts a members Username, Nickname, ID, or Mention to specify a specific user. (Username and Nickname are case and space sensitive)
        If no user is given, selects the invoking user."""

        user = user or ctx.author

        await ctx.trigger_typing()

        async with self.bot.session.get(str(user.avatar_url_as(format='jpeg', static_format='jpeg', size=256))) as r:
            avatar = Image.open(io.BytesIO(await r.read()))

        avatar = ImageOps.fit(avatar, (250, 285))
        background = Image.open('files/images/beautiful/background.jpg')
        background.paste(avatar, (728, 75))
        background.paste(avatar, (728, 675))

        image_bytes = io.BytesIO()
        background.save(image_bytes, format='JPEG')
        image_bytes = image_bytes.getvalue()

        send_file = discord.File(image_bytes, filename='beautiful.jpeg')
        await ctx.send(file=send_file)


    @commands.group(name='images', aliases=['img','imgs','i'], invoke_without_command=True)
    async def custom_images(self, ctx, *, image_name: str):
        """Post custom image commands"""
        if image_name in ['create', 'add', 'remove', 'edit', 'delete', 'info', 'alias', 'aliases', 'list', 'all']:
            return

        images = await self.get_images(image_name, ctx.guild.id)
        if images is None:
            await ctx.send(f'{image_name} does not exist', delete_after=10)
            return
        
        await ctx.send(random.choice(images))
        await self.increment_uses(image_name, ctx.guild.id)
        

    @custom_images.command(name='add', aliases=['create'])
    async def image_create(self, ctx, image_name, *, image_link: str):
        """Creates a custom image command"""
        if image_name in ['create', 'add', 'remove', 'edit', 'delete', 'info', 'alias', 'aliases', 'list', 'all']:
            return

        if not self._link_check.search(image_link) and image_link.startswith('http'):
            await ctx.send("This link can't be used")
            return

        image_check = await self.get_images(image_name, ctx.guild.id)
        if image_check is None:
            await self.new_image(image_name, image_link, ctx.guild.id)
        else:
            image_check.append(image_link)
            await self.update_image(image_name, image_check, ctx.guild.id)
        await ctx.message.add_reaction('\U00002705')

    @custom_images.command(name='remove', aliases=['delete'])
    async def image_delete(self, ctx, image_name, *, image_link: str = None):
        """Delete a custom image command"""
        images = await self.get_images(image_name, ctx.guild.id)
        if len(images) == 0:
            await self.delete_row(image_name, ctx.guild.id)
            await ctx.message.add_reaction('\U00002705')
            return

        if image_link is None:
            await ctx.send('A link from the image group must be supplied', delete_after=15)
            return

        images.remove(image_link)
        if len(images) == 0:
            await self.delete_row(image_name, ctx.guild.id)
            await ctx.message.add_reaction('\U00002705')
            return
        else:
            await self.update_image(image_name, images, ctx.guild.id)
            await ctx.message.add_reaction('\U00002705')

    @custom_images.command(name='list')
    async def image_list(self, ctx, *, image_name: str = None):
        """List the images within a custom image command"""

        if image_name is not None:
            result = await self.get_images(image_name, ctx.guild.id)
            if result is None:
                await ctx.send('No images with that name', delete_after = 15)
                return
        else:
            q = f"""select name from images where guild_id = '{ctx.guild.id}'"""
            values = await self.bot.connection.fetch(q)
            result = []
            for v in values:
                result.append(v['name'])
            result = sorted(result)
            if values is None:
                await ctx.send('No custom images created in this server', delete_after=15)
                return

        page = paginator.Pages(ctx, entries=tuple(result))

        page.embed.set_author(name=f'Custom images in {ctx.guild.name}')

        await page.paginate()

    @custom_images.command(name='info')
    async def image_info(self, ctx, *, image_name: str):
        """Get some info on a custom image command"""
        conn = self.bot.connection
        q = f"""select * from images where guild_id = '{ctx.guild.id}' and name = '{image_name}'"""
        image = await conn.fetchrow(q)
        if image is None:
            await ctx.send('Image not found', delete_after=15)
            return
        e = discord.Embed(colour=discord.Colour.gold())
        e.add_field(name='Name', value=image['name'])
        e.add_field(name='Uses', value=image['uses'])
        e.add_field(name='Number of Images', value=len(image['image_list']))
        e.add_field(name='Created On', value=f"{image['created_at']} UTC")

        await ctx.send(embed=e)


    async def get_images(self, name, guild_id):
        conn = self.bot.connection
        q = f"""select image_list from images where guild_id = '{guild_id}' and name = '{name}'"""
        images = await conn.fetchval(q)
        return images

    async def new_image(self, name, image, guild_id):
        conn = self.bot.connection
        image_list = []
        image_list.append(image)
        q = f"""insert into images (name, image_list, guild_id) VALUES ($1, $2, $3)"""
        insert_status = await conn.execute(q, name, image_list, str(guild_id))

    async def update_image(self, name, images, guild_id):
        conn = self.bot.connection
        get_images_q = f"""update images set image_list = $1 where guild_id = '{guild_id}' and name = '{name}'"""
        status = await conn.fetchval(get_images_q, set(images))
        return status

    async def delete_row(self, name, guild_id):
        conn = self.bot.connection
        delete_row_q = f"""delete from images where guild_id = '{guild_id}' and name = '{name}'"""
        status = await conn.execute(delete_row_q)

    async def increment_uses(self, name, guild_id):
        q = f"""update images set uses = uses+1 where guild_id = '{guild_id}' and name = '{name}'"""
        conn = self.bot.connection
        await conn.execute(q)


def setup(bot):
    bot.add_cog(Images(bot))
