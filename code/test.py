# test.py

# Include relevant libraries.
import os
import random
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Dump file to test different functionality aspects before including them in final bot file.

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

#Quotes
with open('quotes.json', 'r') as quotes_file:
        quotes = json.load(quotes_file)
        responses = quotes
        random.seed(a=None)
        response = random.choice(responses)
        print (response["text"] + ' - ' + response["author"])


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


#Member who has left book club (inc. channel message).

#Choose current book to read.

#Set time to read book.

#Check time to read book.

#Complete book.

#Check current book.

#Check book list.

#Check list of bookworms.
# Check members in book club.
@client.command(pass_context=True)
async def bookworms(ctx):
    role = get(ctx.guild.roles, name=ROLE)
    if role is None:
        print ('There are no Book Worms in this server!')
        return
    empty = True
    for member in ctx.guild.members:
        if role in member.roles:
            MEMBERS = '{} ({}).'.format(member, member.mention)
            embed = discord.Embed(colour = discord.Colour.green(), title="Book Worms (Book Club Members)", description=MEMBERS)
            print (embed=embed)            
        empty = False
    if empty:
        print ("Nobody has the role {}".format(role.mention))


#Alert of time up for book reading.

#Random book picker.

#Random user picker.

#Create / associate with voice channel.