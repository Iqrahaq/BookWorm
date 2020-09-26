# bot.py

# Include relevant libraries.
import os
import mysql.connector
import random
import json
import discord
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

# Use dotenv to conceal token.
load_dotenv()

# Other variables
TOKEN = os.getenv('DISCORD_TOKEN')
ROLE = "Book Worm"
BOOKS = []

mydb = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_DATABASE')
)

# Command prefix
client = commands.Bot(command_prefix = 'bw!')

# Helpful loading prompt.
print("Starting bot...")

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

### See if you can fix this later.
@client.event
async def on_guild_join(guild, ctx):
    default_role = get(ctx.guild.roles, name="BookWorm")
    await ctx.guild.create_role(name=ROLE, colour=discord.Colour(0x00C09A))

# Create role AS SOON AS BOT JOINS.
@client.command()
async def rolesetup(ctx):
    if get(ctx.guild.roles, name=ROLE):
        await ctx.send('Role: "Book Worm" already exists.\nPlease make sure you have this role assigned to join Book Club!')
    else:
        await ctx.guild.create_role(name=ROLE, colour=discord.Colour(0x00C09A))
        await ctx.send('Role created: "Book Worm".\nPlease make sure you have this role assigned to join Book Club!')

@client.command()
async def members(ctx):
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM members")
    myresult = mycursor.fetchall()
    for x in myresult:
        await ctx.send(x)

# Check members in book club.
@client.command(pass_context=True)
async def bookworms(ctx):
    mycursor = mydb.cursor()
    empty = True
    role = get(ctx.guild.roles, name=ROLE)
    if role is None:
        await ctx.send('I can\'t find any "Book Worms"!\nAre you sure you have the correct role? Try running "bw!rolesetup".')
        return
    else:
        embed = discord.Embed(colour = discord.Colour.green(), title="Book Worms (Book Club Members)")
        for member in ctx.guild.members:
            if role in member.roles:
                check_member_sql = 'SELECT * FROM members WHERE member_name=%s AND member_tag=%s'
                val = (str(member), member.mention)
                mycursor.execute(check_member_sql, val)
                members_check = mycursor.fetchall()
                if not members_check:
                    new_member_sql = "INSERT INTO members (member_name, member_tag) VALUES (%s, %s)"
                    mycursor.execute(new_member_sql, val)
                    mydb.commit()
                else:
                    empty = False
        all_members_sql = "SELECT * FROM members"
        mycursor.execute(all_members_sql)
        all_members = mycursor.fetchall()
        for result in all_members:
            var_member_name = result[2].decode()
            var_member_tag = result[3].decode()
            var_member_count = result[4]
            embed.description=('○ {} ({}).- 📚: {}\n'.format(var_member_name, var_member_tag, var_member_count))
    if empty == True:
        embed.description=("Nobody has the role \"{}\"!".format(role))
    await ctx.send(embed=embed)

# Picks random book club member.
@client.command()
async def pickaworm(ctx):
    empty = True
    MEMBERS[:] = []
    role = get(ctx.guild.roles, name=ROLE)
    if role is None:
        await ctx.send('I can\'t find any "Book Worms"!\nAre you sure you have the correct role? Try running "bw!rolesetup".')
        return
    else:
        embed = discord.Embed(colour = discord.Colour.green(), title="Random Book Worm Chosen:")
        for member in ctx.guild.members:
            if role in member.roles:
                if ('○ {} ({}).'.format(member, member.mention)) not in MEMBERS:
                    MEMBERS[0].append('○ {} ({}).'.format(member, member.mention))
                    empty = False
    if empty == True:
        embed.description=("Nobody has the role \"{}\"!".format(role))

    random.seed(a=None)
    response = random.choice(MEMBERS)
    embed.description=(response)
    await ctx.send(embed=embed)


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
