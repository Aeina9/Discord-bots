# This is my first ever personal discord bot made to learn/practice coding! Please be patient with it. Thanks!

# Referenced the following tutorials:
#   https://www.youtube.com/watch?v=SPTfmiYiuok
#   https://www.youtube.com/watch?v=ml-5tXRmmFk

import asyncio
import discord
from discord.errors import ClientException
from discord.ext import commands
import youtube_dl
import os

client = commands.Bot(command_prefix='!', help_command=None)
q = []

# play
@client.command()
async def play(ctx, url:str):
# remove the previously played song, must '!stop' the song before playing another
  try:
    if os.path.isfile('song.m4a'):
      os.remove('song.m4a')
  except PermissionError:
    await ctx.send('**There\'s a song or queue currently playing!\nWait for it to finish, add it to the queue, or use the "!stop" command to end the song/queue!**')
    return

  await ctx.invoke(client.get_command('queue'), url)

# Queue
@client.command()
async def queue(ctx, url:str):

  # if already in the voice channel, don't try to reconnect and play the next song  
  # change 'name' to whichever voice channel you want to join
  try:
    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name = 'Music')
    await voiceChannel.connect()

    queue_msg = discord.Embed(title=':sparkles: Connecting to voice channel. :sparkles:', description='• Use "!help" for command list or other info.', color=discord.Color.green())
    await ctx.send(embed=queue_msg)
  except ClientException:
    pass

  ydl_opts = {
    'format': '140',
  }
  
  with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])

  # Add the latest download to the end of the queue
  latest_song_added = max(os.listdir('./'), key=os.path.getctime)
  if latest_song_added not in q:
    q.append(latest_song_added)
    print(latest_song_added)
    print(q)
  else:
    await ctx.send('**Song link is already in the queue! Feel free to requeue the song after it plays.**')

  # start playing if queueing the first song
  if len(q) == 1:
    await play_queue()

# View the queue list
@client.command()
async def view(ctx):
  if not q:
    await ctx.send('**Queue list is empty!**')
  else:
    q_format=''
    for songs in q:
      q_format = q_format + str(q.index(songs)+1) + '. ' + songs + '\n'
    q_format = q_format.replace('.m4a', '')

    view_msg = discord.Embed(title=':memo: __Queue List__:', description='(Numbers at the end of the YouTube video title reference the specific link used.)\n\n' + q_format, color=discord.Color.green())
    await ctx.send(embed=view_msg)

#remove numbered song on queue list
@client.command()
async def remove(ctx, num:int):
  #(!view to show queue list)
  await ctx.invoke(client.get_command('view'))

  # Confirmation checks and messages 
  if num >= 2:
    await ctx.send('\n**Do you wish to remove **' + '__**' + str(num) + '. ' + str(q[num-1]).replace('.m4a', '') + '**__' + '** from the queue?\nReply with "y" in within 15 seconds or wait to cancel request.**')
    
    def yes(m):
      return m.content == 'y' and m.channel == ctx.channel

    try:
      await client.wait_for('message', check=yes, timeout = 15)
      for file in os.listdir('./'):
        if file == q[num-1]:
          os.remove(file)
          q.pop(num-1)
          await ctx.send("**Song has been removed from the queue.**")
          return
    except asyncio.TimeoutError:
      await ctx.send("**Timed out, canceling remove request.**")

  elif num == 1:
    await ctx.send('**First song is currently playing. To remove/skip, use the "!stop" command!**')
  else:
    await ctx.send('Invalid queue number...')

# repeat -- can't repeat if there is an ongoing queue (!play included), voice must be stopped.
@client.command()
async def repeat(ctx):
  if not q:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
      voice.stop()
    elif not voice.is_connected():
      await ctx.send('**I\'m not connected to a voice channel!**')
      return
    voice.play(discord.FFmpegOpusAudio('song.m4a'))

    # since original song title gets replaced, this will do...
    q.append('!repeat command executed - last song played')
    while voice.is_playing() or voice.is_paused():
      await asyncio.sleep(1)
    q.pop(0)
    await play_queue()
  else:
    await ctx.send('**Can\'t repeat in the middle of a song or queue...\nIf there\'s a queue currently playing, feel free to queue the song again after it\'s played or stopped!**\n\n*(P.S. Songs from "!play" are in a queue, try using "!stop" followed by "!repeat".)*')

# leave voice channel
@client.command()
async def leave(ctx):
  voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
  # clear the queue when leaving
  if q:
    for file in os.listdir('./'):
      if file.endswith('.m4a') and not file.startswith('song.m4a'):
        os.remove(file)
        q.clear()
        voice.stop
  try:
    if voice.is_connected():
      # The current song couldn't be deleted in the code above because it was in use. Delete that now.
      os.listdir('./').remove('song.m4a')
      await voice.disconnect()
  except AttributeError:
    await ctx.send('**I\'m not connected to a channel!**')
    
# pause song
@client.command()
async def pause(ctx):
  voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
  if voice.is_playing():
    voice.pause()
  else:
    await ctx.send('**There\'s no music playing at the moment!**')

# resume song
@client.command()
async def resume(ctx):
  voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
  if voice.is_paused():
    voice.resume()
  else:
    await ctx.send('**The music isn\'t paused!**')

# stop song
@client.command(aliases = ['skip'])
async def stop(ctx):
  voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
  voice.stop()

@client.command()
async def help(ctx):
  help_msg = discord.Embed(title=':memo: __Command List:__', description='• !play + YouTube link (play song)\n• !pause (pause song)\n• !resume (resume song)\n• !queue + YouTube link (queue songs)\n• !view (view queue list)\n• !remove + number on queue list (removes song on queue list)\n• !repeat (repeats song last played)\n• !stop, !skip (moves on from current song, -will go to next song in queue if possible)\n• !leave (leave voice channel, -resets queue)\n• !help (shows this message)', color=discord.Color.green())
  await ctx.send(embed=help_msg)

  other_info_msg = discord.Embed(title=':memo:__Other Info__:', description=':x: Can only play single YouTube links (No playlists, streams, or YouTube Lives)\n:x: No more than one command a message. Only the first will execute.\n:x: Bot will disconnect from voice channel after 30 minutes of voice inactivity.\n:x: In case of bugs/errors, try to "!leave" and continue where you left off.\n:x: If that doesn\'t work, please come back and try later!**\n\n:robot: *(Dev note) This is my first ever discord bot made to learn/practice coding!\n:woman_bowing: Please be patient with it. Thanks!*', color=discord.Color.green())
  await ctx.send(embed=other_info_msg)

@client.event
# Start up
async def on_ready():
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!play"))
  print('Logged in as {0.user}'.format(client))

  # clear any songs from the folder upon boot up
  for file in os.listdir('./'):
    if file.endswith('.m4a'):
      os.remove(file)

# queue fn
async def play_queue():
  global last_played
  if not q:
    return

  # delete the song that just finished playing from the folder.
  voice = discord.utils.get(client.voice_clients)
  if os.path.isfile('song.m4a'):
    os.remove('song.m4a')
  
  # find the first song in queue
  for file in os.listdir('./'):
    if file == q[0]:
      os.rename(file, 'song.m4a')
      obj = object()
      last_played = id(obj)
      
  # play song in queue, and wait for the song to finish/!stop (not incl. pausing)
  # pop off the first item in the queue and recurse if queue has more songs
  # errors may be from exiting the queue while it is playing
  try:
    voice.play(discord.FFmpegOpusAudio('song.m4a'))
    print('Now playing next queue...')
    while voice.is_playing() or voice.is_paused():
      await asyncio.sleep(1)
    q.pop(0)
    # continue or timeout
    if q:
      await play_queue()
    else:
      try:
        await asyncio.sleep(1800)
        if last_played == id(obj):
          os.remove('song.m4a')
          print('Timeout disconnect.')
          await voice.disconnect()
      except PermissionError:
          pass
  except AttributeError:
    pass

client.run(os.getenv('token'))
