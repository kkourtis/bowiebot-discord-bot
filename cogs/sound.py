# sound.py
# this is going to be one hell of a ride

import discord
from discord.ext import commands
import asyncio
from collections import deque
import os
from cogs.utils import prefix, paginator
import random
from tinytag import TinyTag
import time

import io
import zipfile
import shutil

import subprocess

import aiohttp

class SoundFile:
    def __init__(self, name, path, channel, length):
        self.name = name
        self.path = path
        self.channel = channel
        self.length = length

class Player:
    def __init__(self, bot, voice_client, channel, playlist):
        self.bot = bot
        self.loop = bot.loop
        self.voice_client = voice_client
        self.channel = channel
        self.playlist = playlist

class Sound(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._players = {}
        self._custom_path = '/mnt/volume_nyc3_01/bowiebot_files/custom_sounds'
        self._explicit_disallowed_char = ["/","\\", "?", '%', '*', ':', '|', '"', '<', '>', '.', '\n', '\t', '\0', ' ', '`', ';', ')','(']
        self._dissallowed_command_name = ['add','all','remove','delete','list','rename','move']
        self._allowed_sound_ext = ['.mp3', '.ogg','.wav']

        self._description = """Plays sound clips in a voice channel"""
        self._short_description = "\n".join(self._description.splitlines()[0:1])

    async def plonk_check(self, user, message):
        """Checks if a user has been plonked"""
        q = f"select user_id, guild_id from plonks where " \
            f"user_id = '{message.author.id}' and guild_id = '{message.guild.id}'" \
            f"or user_id = '{message.author.id}' and guild_id IS NULL"
        value = await self.bot.pool.fetchrow(q)  
        try:
            if value['guild_id'] == str(message.guild.id) or value['guild_id'] is None:
                return True
        except:
            return False

    async def get_file_length(self,path):
        try:
            tag = TinyTag.get(path)
        except Exception as e: 
            print(e)
            return 0 #TODO: Actually pass the error
        return tag.duration

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.content == '' or message.author.voice is None or message.guild is None:
            return

        content = await prefix.remove_prefix_from_message(self.bot, message)
        if content is None:
            return

        if content.split()[0] in os.listdir('files/sound'):
            if await self.plonk_check(message.author, message):
                return
            await self.parse(content, message)

    async def parse(self, command, message, custom = False):
        sound = await self.get_sound(command.split(), message, custom)
        player = await self.connect(message)
        player.playlist.append(sound)
        if player.voice_client.is_playing():
            return
        else:
            await self.play(player)

    async def get_sound(self, command, message, custom = False):
        if len(command) == 1:
            if custom:
                sound_file_list = os.listdir(f'{self._custom_path}/{message.guild.id}/{command[0]}')
            elif not custom:
                sound_file_list = os.listdir(f'files/sound/{command[0]}')
            sound_file = random.choice(sound_file_list)
            command = command[0]
        elif len(command) == 2:
            sound_file = command[1]
            command = command[0]   
        if not custom: 
            path = f'files/sound/{command}/{sound_file}'
        elif custom:
            path = f'{self._custom_path}/{message.guild.id}/{command}/{sound_file}'

        sound_file_length = await self.get_file_length(path)
        if sound_file_length == 0:
            print('haha no length')
            return

        print(path)
        return SoundFile(command, path, message.author.voice.channel, sound_file_length)

    async def connect(self, message):
        for client in self.bot.voice_clients:
            if client.guild.id == message.guild.id:
                if message.guild.id in self._players:
                    return self._players[message.guild.id]
                else:
                    await client.disconnect(force=True)
            break

        try:
            voice = await message.author.voice.channel.connect()
        except:
            for client in self.bot.voice_clients:
                if client.guild.id == message.guild.id:
                    await client.disconnect(force=True)
                    voice = await message.author.voice.channel.connect()
        self._players[message.guild.id] = Player(self.bot, voice, message.author.voice.channel, deque())
        return self._players[message.guild.id]

    async def disconnect(self, message):
        try:
            del self._players[message.guild.id]
        except:
            pass

        for client in self.bot.voice_clients:
            if message.guild.id == client.guild.id:
                await client.disconnect(force=True)

    async def play(self, player):
        """Double check if we are playing"""
        if player.voice_client.is_playing():
            return
        
        """Double check disconnect if playlist is empty"""
        if len(player.playlist) == 0:
            await self.disconnect(player.voice_client.channel)
        
        """Get the next sound"""
        sound = player.playlist[0]

        """Move to the correct channel"""
        #if player.voice_client.channel is not sound.channel:
         #   await player.voice_client.move_to(sound.channel)

        player.voice_client.play(discord.FFmpegPCMAudio(sound.path))
        player.voice_client.source = discord.PCMVolumeTransformer(player.voice_client.source)
        player.voice_client.source.volume = 0.25

        await asyncio.sleep(sound.length+0.75)

        if sound in player.playlist:
            await self.after_play(player, sound)
        else:
            return

    async def after_play(self, player, sound = None):
        if sound is not None:
            if sound not in player.playlist:
                return

        player.playlist.popleft()

        if len(player.playlist) == 0:
            await self.disconnect(player.voice_client.channel)
            return
        
        await self.play(player)

    @commands.command(hidden=True)
    async def skip(self, ctx):
        """Stop the currently playing sound and play the next"""
        if ctx.author.voice is None:
            return

        for i in self.bot.voice_clients:
            if ctx.author.voice_channel == i.channel:
                if ctx.guild.id in self._players:
                    self._players[ctx.guild.id].voice_client.stop()
                    await self.after_play(self._players[ctx.guild.id])
                    return

    @commands.command()
    async def stop(self, ctx):
        """Stops playing, clears the queue, disconnects"""
        if ctx.author.voice is None: 
            return
        
        for i in self.bot.voice_clients:
            if ctx.author.voice.channel == i.channel:
                if ctx.guild.id in self._players:
                    self._players[ctx.guild.id].voice_client.stop()
                    self._players[ctx.guild.id].playlist.clear()
                    await self.disconnect(self._players[ctx.guild.id].voice_client.channel)
                    return

    @commands.command(name='disconnect', hidden=True)
    async def force_disconnect(self, ctx):
        """Force Bowie Bot to disconnect"""
        await self.disconnect(ctx.message)

    @commands.command(name='queue')
    async def check_queue(self,ctx):
        """Displays the current queue of sounds to be played"""
        try:
            await ctx.send(self._players[ctx.guild.id].playlist)
        except:
            await ctx.send("There is nothing in the queue")
    
    @commands.command(name='list')
    async def list_commands(self, ctx, command = None):
        """Lists all possible sound commands"""
        msg = '```Markdown\n'
        if command is not None:
            path = f"files/sound/{command}"
            entries = sorted(os.listdir(path))
            await self.build_sound_file_list(ctx, command, path)
            return
        else:
            entries = sorted(os.listdir(f"files/sound"))
            for pos in range(0, len(entries)):
                if pos % 5 == 0 and pos is not 0:
                    msg += '\n'
                msg += f"{entries[pos]:<15} "
        await ctx.send(msg+'```')

    async def build_sound_file_list(self, ctx, command, path):
        page = paginator.Pages(ctx, entries=tuple(os.listdir(path)))
        page.embed.set_author(name=f"Files in {command}")
        await page.paginate()

###### BEGIN CUSTOM SOUND IMPLEMENTATION ######

    @commands.group(name='sound', aliases=['s'], invoke_without_command = True)
    async def custom_sound(self, ctx, command: str, file_name: str = None):
        """Plays a custom sound"""

        if ctx.invoked_subcommand is not None:
            return

        if command in ['add','remove','delete','move']:
            return

        if os.path.exists(f'{self._custom_path}/{ctx.guild.id}/{command}'):
            if file_name is not None:
                command = command+f' {file_name}'
            await self.parse(command, ctx.message, True)

    @custom_sound.command(name='list')
    async def list_custom_sounds(self, ctx, command:str = None):
        """Lists all custom sounds"""
        msg = '```Markdown\n'
        if command is None:
            msg = f"Custom Commands in {ctx.message.guild.name}" + msg
            path = f'{self._custom_path}/{ctx.guild.id}'
            entries = sorted(os.listdir(path))
            for pos in range(0, len(entries)):
                if pos % 5 == 0 and pos is not 0:
                    msg += '\n'
                msg += f"{entries[pos]:<15} "
        else:
            path = f'{self._custom_path}/{ctx.guild.id}/{command}'
            entries = sorted(os.listdir(path))
            await self.build_sound_file_list(ctx, command, path)
            return
        await ctx.send(msg+'```')
        return

    @custom_sound.command(name = 'add')
    async def add_custom_sound(self, ctx, command: str):
        """Add a custom sound to the server
        Accepts .zip, .mp3, .wav, .ogg"""
        if len(ctx.message.attachments) == 0:
            await ctx.send('You must upload a sound file or zip as an attachment along with the command')            
            return

        if len(command) > 15:
            await ctx.send('Command name is too long (15 character max)')
            return

        path = f'{self._custom_path}/{ctx.guild.id}/{command}'

        command = await self.clean_command_name(command)
        if command not in os.listdir(f'{self._custom_path}/{ctx.guild.id}'):
            if await self.command_name_not_allowed(ctx, command):
                return
            os.mkdir(path)

        attachments = await self.remove_bad_attachments(ctx)
        
        for attachment in attachments:
            if attachment.filename[-4:] == '.zip':
                await self.parse_zip_file(path, attachment, ctx)
            if attachment.filename[-4:] in self._allowed_sound_ext:
                await self.parse_file(path, attachment, ctx, command)

    @custom_sound.group(name = 'remove', invoke_without_command=True)
    async def remove_custom_sound(self,ctx,command:str,file_name:str):
        """Removes a sound from a command"""
        if ctx.invoked_subcommand is not None: return
        if file_name[-4:] not in self._allowed_sound_ext:
            await ctx.send("Please specify the file extension")
            return

        file_path = f"{self._custom_path}/{str(ctx.guild.id)}/{command}/{file_name}"
        
        if not os.path.exists(file_path):
            await ctx.send(f'The path {str(ctx.guild.id)}/{command}/{file_name} does not exist')
            return
        else:
            os.remove(file_path)
            dir_del = await self.delete_folder_if_empty(f"{self._custom_path}/{str(ctx.guild.id)}/{command}")
            if not os.path.exists(file_path):
                msg = f"Successfully removed `{file_name}` from `{command}`"
                if dir_del is True:
                    msg+=f"\nNo other sounds associate with `{command}`, command removed"
                await ctx.send(msg)
                return
            else:
                await ctx.send(f"Unable to remove `{file_name}` from `{command}`")
                return

    @remove_custom_sound.command(name='all')
    async def remove_all_sounds_from_command(self, ctx, command:str):
        """Remove all files from a command"""
        path = f"{self._custom_path}/{str(ctx.guild.id)}/{command}"
        removed = 0
        msg = ''
        total_files = len(os.listdir(path))

        if not os.path.exists(path):
            await ctx.send(f"{command} is not a command")
            return
        else:
            for f in os.listdir(path):
                os.remove(f"{path}/{f}")
                if os.path.exists(f"{path}/{f}"):
                    msg += f"Failed to remove `{f}`\n"
                    continue
                removed = removed+1
        msg += f"Removed `{removed}` of `{total_files}` files"
        await self.delete_folder_if_empty(path)
        await ctx.send(msg)

    async def parse_file(self, path, attachment, ctx, command):
        path = f'{path}/{attachment.filename}'
        await attachment.save(path)
        if not os.path.exists(path):
            await ctx.send('file failed to save')
            return
        length_check, response = await self.check_length(path)
        if not length_check:
            os.remove(path)
            await self.delete_folder_if_empty(path)
            await ctx.send(f'file failed: {response}')
        else:
            await ctx.send(f"""File `{attachment.filename}` succeeded with a length of {response}: You can call this file specifically with `{ctx.prefix}sound {command} {attachment.filename}` or if you just call `{ctx.prefix}sound {command}` it has a chance to randomly play if there are other sounds within that command""")

    async def parse_zip_file(self, path, attachment, ctx):
        recieve = time.time()
        file_bytes = io.BytesIO()
        await attachment.save(file_bytes)
        zip_bytes = zipfile.ZipFile(file_bytes)
        files, failed_files = await self.parse_zip_bytes(path, zip_bytes)       
        del zip_bytes
        if len(os.listdir(path)) == 0:
            await ctx.send('File failed to save')
            return
        total_files = len(files) + len(failed_files)
        msg = ''
        if failed_files is not []:
            for i in failed_files:
                msg += f"`{i}` failed: {i[1]}\n"
        good_files = []
        for i in files:
            length_check, response = await self.check_length(f'{path}/{i}')
            if not length_check:
                os.remove(f'{path}/{i}')
                msg += f'`{i} failed: {response}\n'
            else:
                good_files.append(i)
            await self.delete_folder_if_empty(path)
            msg += f"""`{len(good_files)}` of `{total_files}` files suceeded"""
            msg += f'\nTime elapsed: {round(time.time() - recieve,2)} seconds'
            if len(msg) > 2000:
                msg = f"`{len(good_files)}` of `{total_files}` files suceeded\nTime elapsed: {round(time.time() - recieve,2)} seconds"
            await ctx.send(msg)

    async def parse_zip_bytes(self, path, zip_bytes):
        extracted_files = []
        failed_files = []
        for i in zip_bytes.namelist():
            filename = os.path.basename(i)
            if not filename:
                continue
            if filename[-4:] not in self._allowed_sound_ext:
                failed_files.append((filename, 'File is not a recognized extension'))
                continue
            extracted_files.append(filename)
            source = zip_bytes.open(i)
            target = open(os.path.join(path, filename), 'wb')
            with source, target:
                shutil.copyfileobj(source, target)
            target.close()
        return extracted_files, failed_files

    async def check_length(self, path):
        vlen = None
        if path[-4:] in self._allowed_sound_ext:
            tag = TinyTag.get(path)
            vlen = tag.duration
        else:
            return False, f'File is not a sound file somehow getting this far'

        if vlen is not None:
            vlen = round(vlen, 2)
            if vlen < 16:
                return True, vlen
            else:
                return False, f'File is over 15 seconds in length. The file is {vlen} seconds in length'
        else:
            return False, 'File length check unable to be run on this file. File may not be an MP3.'

    async def delete_folder_if_empty(self, path):
        if os.path.exists(path) and len(os.listdir(path)) == 0:
            os.rmdir(path)
            return True
        else:
            return False

    async def remove_bad_attachments(self, ctx):
        good_attachments = []
        bad_attachments = []
        for attachment in ctx.message.attachments:
            a_name = attachment.filename.split('.')
            if not a_name[-1] in ['mp3', 'wav', 'ogg', 'zip', '7z']:
                await ctx.send(f".{a_name[-1]} is an unsupported file type")
                bad_attachments.append(attachment)
            else:
                good_attachments.append(attachment)
        return good_attachments

    async def attachment_not_allowed(self, ctx):
        for attachment in ctx.message.attachments:
            a_name = attachment.filename.split('.')
            if not a_name[-1] in ['mp3', 'wav', 'ogg', 'zip', '7z']:
                await ctx.send(f".{a_name[-1]} is an unsupported file type")
                return True

    async def command_name_not_allowed(self, ctx, command):
        if command in self._dissallowed_command_name:
            await ctx.send("Command name cannot collide with a name in use")
            return True
        if await self.command_name_too_long(command):
            await ctx.send("Command name is too long (15 character max)")
            return True

    async def clean_command_name(self, command):
        command = command.strip()
        command = await self.remove_dissallowed_char(command)
        return command

    async def command_name_too_long(self, command_name):
        if len(command_name) > 15:
            return True
        else:
            return False

    async def remove_dissallowed_char(self, tar):
        for char in self._explicit_disallowed_char:
            tar = tar.replace(char, '_')
        return tar

def setup(bot):
    bot.add_cog(Sound(bot))