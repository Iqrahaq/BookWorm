# bot.py

# Include relevant libraries.
import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Use dotenv to conceal token.
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
client = commands.Bot(command_prefix = 'bw!')

# Helpful loading prompt.
print("Starting bot...")

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

# Ping to answer with the ms latency, helpful for troubleshooting.
@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round (client.latency * 1000)}ms ')

# Answers with a random quote - quote.txt needs to be created.
@client.command()
async def quote(ctx):
    responses = open('quotes.txt').read().splitlines()
    random.seed(a=None)
    response = random.choice(responses)
    await ctx.send(response)

# Error checking.
@client.event
async def on_command_error(ctx, error):
    await ctx.send(f'Error. Try bw!help ({error})')

# Remove default help command to allow for bw!help.
client.remove_command('help')

# Help list and details of commands.
@client.command(pass_context=True)
async def help(ctx):
    embed = discord.Embed(
    	colour = discord.Colour.green())
    embed.set_author(name='Help : list of commands available')
    embed.add_field(name='bw!ping', value='Returns bot respond time in milliseconds', inline=False)
    embed.add_field(name='bw!ping', value='Returns bot respond time in milliseconds', inline=False)
    embed.add_field(name='bw!ping', value='Returns bot respond time in milliseconds', inline=False)
    await ctx.send(embed=embed)


client.run(TOKEN)
