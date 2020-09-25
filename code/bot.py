# bot.py

# Include relevant libraries.
import os
import random
import json
import discord
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

# Use dotenv to conceal token.
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ROLE = "Book Worm"
client = commands.Bot(command_prefix = 'bw!')

# Helpful loading prompt.
print("Starting bot...")

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

guild = ctx.guild
await guild.create_role(name=ROLE, colour=discord.Colour(0x00EE00))

# Ping to answer with the ms latency, helpful for troubleshooting.
@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round (client.latency * 1000)}ms ')

# Answers with a random quote - using quotes.json.
@client.command()
async def quote(ctx):
    with open('quotes.json', 'r') as quotes_file:
        quotes = json.load(quotes_file)
        responses = quotes
        random.seed(a=None)
        response = random.choice(responses)
    await ctx.send(response["text"] + ' - ' + response["author"])


#Member has joined book club (via channel or bookworm tag) (inc. channel message)
@client.command(pass_context=True)
async def getuser(ctx, role: discord.Role):
    role = discord.utils.get(ctz.message.server.roles, name="BookWorm")
    if role is None:
        await bot.say('There are no "BookWorms" in this server! ¯\\_(ツ)_/¯')
        return
    empty = True
    for member in ctx.message.server.members:
        if role in member.roles:
            await bot.say("{0.name}: {0.id}, Welcome to Book Club!".format(member))
            empty = False
    if empty:
        await bot.say("Nobody has the role {}".format(role.mention))


# Error checking...
@client.event
async def on_command_error(ctx, error):
    await ctx.send(f'Error. Try bw!help ({error})')

# Remove default help command to allow for bw!help.
client.remove_command('help')

# Help list and details of commands...
@client.command(pass_context=True)
async def help(ctx):
    embed = discord.Embed(
    	colour = discord.Colour.green())
    embed.set_author(name='Help : list of commands available')
    embed.add_field(name='bw!ping', value='Returns bot respond time in milliseconds', inline=False)
    embed.add_field(name='bw!quote', value='Returns an inspirational quote.', inline=False)
    await ctx.send(embed=embed)

#token
client.run(TOKEN)
