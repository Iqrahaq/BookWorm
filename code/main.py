# main.py

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import csv
import time

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

# Load cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


# Set custom status for bot.
async def custom_status():
    while True:
        with open('books.csv', 'r') as books_file:
            books = csv.reader(books_file)
            next(books_file)
            for book in books:
                if any(book):
                    book_name = book[0]
                    book_authors = book[1]
                    book_url = book[5]
                    await client.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, state="Listening", name="'{0}' by {1}. 🎧".format(book_name, book_authors)))
                    await asyncio.sleep(15000)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    client.loop.create_task(custom_status())

# token
client.run(TOKEN, reconnect=True)