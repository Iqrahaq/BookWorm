# main.py

import discord
from discord.ext import commands, tasks
import os
import sys
from dotenv import load_dotenv
import asyncio
import csv
import time
import traceback

# Use dotenv to conceal token.
load_dotenv()

# Other necessary variables 
TOKEN = os.getenv('DISCORD_TOKEN')
ROLE = "Book Worm"
MEMBERS = []
CURRENT_BOOK = None
NO_AUTHORS = False
BOOKS_RESULTS = []

intents = discord.Intents.default()
intents.members = True

# Command prefix
client = commands.Bot(command_prefix='bw!', intents=intents)

# Helpful loading prompt.
print("Starting bot...")

# Remove default help command to allow for bw!help.
client.remove_command('help')

# Error checking...
@client.event
async def on_command_error(ctx, error):
    await ctx.send(f'Error. Try bw!help ({error})')
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

# Load cogs
for filename in os.listdir('/home/bookworm/code/cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

# Set custom status for bot.
async def custom_status():
    await client.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, name=" an Audio Book. 🎧"))
                    
# @tasks.loop(seconds=5)
# async def daily_quote(ctx):
#     daily_command = client.get_command(name='post_daily_quote')
#     await daily_command.callback(ctx)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    daily_quote.start()
    await custom_status()

# token
client.run(TOKEN, reconnect=True)
