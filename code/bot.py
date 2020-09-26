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
MEMBERS = []
client = commands.Bot(command_prefix = 'bw!')

# Helpful loading prompt.
print("Starting bot...")

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


# Create role AS SOON AS BOT JOINS.
@client.command()
async def rolesetup(ctx):
    if get(ctx.guild.roles, name=ROLE):
        await ctx.send('Role: "Book Worm" already exists')
    else:
        await ctx.guild.create_role(name=ROLE, colour=discord.Colour(0x00C09A))
        await ctx.send('Role created: "Book Worm". Please make sure you have this role to join Book Club!')


# Check members in book club.
@client.command(pass_context=True)
async def bookworms(ctx):
    role = get(ctx.guild.roles, name=ROLE)
    if role is None:
        await ctx.send('There are no Book Worms in this server!')
        return
        empty = True
    else:
        for member in ctx.guild.members:
            if role in member.roles:
                MEMBERS.append('○ {} ({}).'.format(member, member.mention))
                empty = False
        embed = discord.Embed(colour = discord.Colour.green(), title="Book Worms (Book Club Members)", description='\n'.join(MEMBERS))
        await ctx.send(embed=embed)          
    if empty:
        await ctx.send("Nobody has the role {}".format(role.mention))
    

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



# Returns information about bot.
@client.command(pass_context=True)
async def info(ctx):
    embed = discord.Embed(colour = discord.Colour.green())
    embed=discord.Embed(title='BookWorm (Bot)', url='https://github.com/Iqrahaq/BookWorm', description='A bot to help contribute to book club activities.', color=0x5ae000)
    embed.set_author(name='Iqra Haq', url='https://www.iqrahaq.com')
    embed.set_thumbnail(url='https://github.com/Iqrahaq/BookWorm/raw/master/vector/bookworm-01.png')
    embed.add_field(name='How to use?', value='Use the "bw!help" command!')
    await ctx.send(embed=embed)



# Error checking...
@client.event
async def on_command_error(ctx, error):
    await ctx.send(f'Error. Try bw!help ({error})')

# Remove default help command to allow for bw!help.
client.remove_command('help')

# Help list and details of commands...
@client.command(pass_context=True)
async def help(ctx):
    embed = discord.Embed(colour = discord.Colour.green())
    embed.set_author(name='Help - List of commands available: ')
    embed.add_field(name='bw!ping', value='Returns bot respond time in milliseconds.', inline=False)
    embed.add_field(name='bw!info', value='Returns information about the bot.', inline=False)
    embed.add_field(name='bw!bookworms', value='Returns a list of the current book club members.', inline=False)
    embed.add_field(name='bw!quote', value='Returns an inspirational quote.', inline=False)
    await ctx.send(embed=embed)

#token
client.run(TOKEN)
