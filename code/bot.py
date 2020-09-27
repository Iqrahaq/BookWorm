# bot.py

# Include relevant libraries.
import os
import mysql.connector
import random
import json
import isbnlib
from isbnlib import *
import discord
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import asyncio


# Use dotenv to conceal token.
load_dotenv()

# Other variables
TOKEN = os.getenv('DISCORD_TOKEN')
ROLE = "Book Worm"
MEMBERS = []
CURRENT_BOOK_TITLE = []
CURRENT_BOOK_AUTHOR = []
BOOK_RESULTS_COUNT = []
BOOKS_RESULTS = []

#DB connectivity
mydb = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_DATABASE')
)

mycursor = mydb.cursor(buffered=True)

# Command prefix
client = commands.Bot(command_prefix = 'bw!')

# Helpful loading prompt.
print("Starting bot...")

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.command()
async def botsetup(ctx):
    GUILD = ctx.guild.id
    default_role = get(ctx.guild.roles, name="BookWorm")
    mycursor.execute("USE {}".format(mydb.database))
    mycursor.execute('SHOW TABLES')
    all_tables = mycursor.fetchall()
    for table in all_tables:
        if table is not GUILD or all_tables is empty:
            mycursor.execute("CREATE TABLE IF NOT EXISTS GUILD_{} (member_id INT(100) NOT NULL AUTO_INCREMENT, guild_id VARCHAR(100) DEFAULT NULL, member_name VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL, member_tag VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL, member_count INT(5) DEFAULT '0', member_books VARCHAR(1000) DEFAULT NULL, PRIMARY KEY(member_id)) ".format(GUILD))
            mydb.commit()
            mycursor.execute("SELECT * FROM guilds WHERE guild_id={}".format(GUILD))
            guilds_check = mycursor.fetchone()
            if not guilds_check:
                new_guild_sql = 'INSERT INTO guilds (guild_id, guild_name) VALUES (%s, %s)'
                val = (str(GUILD), str(ctx.guild.name))
                mycursor.execute(new_guild_sql, val)
                mydb.commit()
    
    if get(ctx.guild.roles, name=ROLE):
        await ctx.send('Role: "Book Worm" already exists.\nPlease make sure you have this role assigned to join Book Club!')
    else:
        await ctx.guild.create_role(name=ROLE, colour=discord.Colour(0x00C09A))
        await ctx.send('Role created: "Book Worm".\nPlease make sure you have this role assigned to join Book Club!')


@client.command()
async def members(ctx):
    mycursor.execute("SELECT * FROM members")
    myresult = mycursor.fetchall()
    for x in myresult:
        await ctx.send(x)

# Check members in book club.
@client.command(pass_context=True)
async def bookworms(ctx):
    empty = True
    role = get(ctx.guild.roles, name=ROLE)
    if role is None:
        await ctx.send('I can\'t find any "Book Worms"!\nAre you sure you have the correct role? Try running "bw!rolesetup".')
        return
    else:
        for member in ctx.guild.members:
            check_member_sql = 'SELECT * FROM GUILD_{} WHERE member_tag=%s'.format(ctx.guild.id)
            val = (str(member.mention))
            mycursor.execute(check_member_sql, val)
            members_check = mycursor.fetchall()
            if role in member.roles:
                if not members_check:
                    new_member_sql = 'INSERT INTO GUILD_{} (guild_id, member_name, member_tag) VALUES (%s, %s, %s)'.format(ctx.guild.id)
                    val = (str(ctx.guild.id), str(member), str(member.mention))
                    mycursor.execute(new_member_sql, val)
                    mydb.commit()
                    empty = False
                else:
                    empty = False
            else:
                check_member_sql = 'DELETE FROM GUILD_{} WHERE member_tag=%s'.format(ctx.guild.id)
                val = (str(member.mention))
                mycursor.execute(check_member_sql, val)
                mydb.commit()
    if empty == True:
        await ctx.send("Nobody has the role \"{}\"!".format(role))

    embed = discord.Embed(colour = discord.Colour.green(), title="Book Worms (Book Club Members)")
    all_members_sql = 'SELECT * FROM GUILD_{}'.format(ctx.guild.id)
    mycursor.execute(all_members_sql)
    all_members = mycursor.fetchall()
    for result in all_members:
        var_member_name = result[2].decode()
        var_member_tag = result[3].decode()
        var_member_count = result[4]
        embed.add_field(name='○ {}'.format(var_member_name), value='({})\n 📚: {}\n\n'.format(var_member_tag, var_member_count), inline=False)
    await ctx.send(embed=embed)


# Picks random book club member.
@client.command()
async def pickaworm(ctx):
    MEMBERS[:] = []
    empty = True
    role = get(ctx.guild.roles, name=ROLE)
    if role is None:
        await ctx.send('I can\'t find any "Book Worms"!\nAre you sure you have the correct role? Try running "bw!rolesetup".')
        return
    else:
        all_members_sql = 'SELECT * FROM GUILD_{}'.format(ctx.guild.id)
        mycursor.execute(all_members_sql)
        all_members = mycursor.fetchall()
        for result in all_members:
            var_member_name = result[2].decode()
            var_member_tag = result[3].decode()
            MEMBERS.append('○ {} ({}).\n'.format(var_member_name, var_member_tag))
            empty = False

    if empty == True:
        await ctx.send("Nobody has the role \"{}\"!".format(role))

    embed = discord.Embed(colour = discord.Colour.green(), title="Random Book Worm Chosen:")
    random.seed(a=None)
    response = random.choice(MEMBERS)
    embed.description=(response)
    await ctx.send(embed=embed)


# Searches for book (generic compared to setbook).
@client.command()
async def booksearch(ctx):
    await ctx.send(f'{ctx.author.mention}, what\'s the book called?')
    def check(message):
        return message.channel == ctx.channel
    try:
        current_message = await client.wait_for('message', check=check, timeout=30)
        book_results = goom(current_message.content)
        if book_results:
            book_results_count = len(book_results)
            embed = discord.Embed(colour = discord.Colour.green(), title="Book Results:")
            i = 1
            while i < book_results_count:
                for book in book_results:
                    embed.add_field(name='{}. {} ({})'.format(i, book['Title'], book['Year']), value=', '.join(book['Authors']), inline=False)
                    i+=1
            embed.set_footer(text="{} books found!\nCouldn't find the book? Try \"bw!booksearch\" again but with more precision 😉".format(book_results_count))
            await ctx.send(embed=embed)
        else:
            await ctx.send("I couldn't find any books. ¯\\_(ツ)_/¯")
    except asyncio.TimeoutError as e:
        print(e)
        await ctx.send("Response timed out.")

@client.command()
async def setbook(ctx):
    await ctx.send(f'{ctx.author.mention}, what\'s the book called?')
    def check(message):
        return message.channel == ctx.channel
    try:
        current_message = await client.wait_for('message', check=check, timeout=30)
        book_results = goom(current_message.content)
        if book_results:
        	book_results = goom(current_message.content)
        if book_results:
            book_results_count = len(book_results)
            embed = discord.Embed(colour = discord.Colour.green(), title="Book Results:")
            i = 1
            while i < book_results_count:
                for book in book_results:
                	if 'ISBN-10' in book:
                		BOOK_CHOICE = book['ISBN-10']
                	elif 'ISBN-13' in book:
                		BOOK_CHOICE = book['ISBN-13']
                	BOOKS_RESULTS.append(BOOK_CHOICE)
                	embed.add_field(name='{}. {} ({})'.format(i, book['Title'], book['Year']), value=', '.join(book['Authors']), inline=False)
                	i+=1
            embed.set_footer(text="{} books found!\n".format(book_results_count))
            await ctx.send(embed=embed)
        else:
            await ctx.send("I couldn't find any books. ¯\\_(ツ)_/¯")
    except asyncio.TimeoutError as e:
        print(e)
        await ctx.send(f'{ctx.author.mention}, you took a while to respond... 🤔')

    await ctx.send(f'{ctx.author.mention}, is your book in the results list? [yes or no]')
    def check(message):
    	return message.channel == ctx.channel and message.author == ctx.author
    try:
    	current_message = await client.wait_for('message', check=check, timeout=1000)
    	if current_message.content == "y" or current_message.content == "yes" or current_message.content == "YES" or current_message.content == "Y":
    		await ctx.send(f'{ctx.author.mention}, what number is it?')

    		await ctx.send(f'{ctx.author.mention}, is your book in the results list? [yes or no]')
    		def check(message):
    			return message.channel == ctx.channel and message.author == ctx.author
    		try:
    			current_message = await client.wait_for('message', check=check, timeout=30)
    			BOOK_CHOICE = (int(current_message.content)-1)
    			print(BOOKS_RESULTS)
    			print(BOOK_CHOICE)
    			embed = discord.Embed(colour = discord.Colour.green(), title="{}'s Chosen Book:".format(ctx.author))
    			CHOSEN_BOOK = meta(BOOKS_RESULTS[BOOK_CHOICE])
    			embed.add_field(name='{} ({})'.format(CHOSEN_BOOK['Title'], CHOSEN_BOOK['Year']), value=', '.join(CHOSEN_BOOK['Authors']), inline=False)
    			thumbnail = cover(BOOKS_RESULTS[BOOK_CHOICE])
    			embed.set_thumbnail(url='{}'.format(thumbnail['thumbnail']))
    			await ctx.send(embed=embed)
    		except asyncio.TimeoutError as e:
    			print(e)
    			await ctx.send(f'{ctx.author.mention}, you took a while to respond... 🤔')
    	else:
    		await ctx.send(f'{ctx.author.mention}, maybe try \"bw!setbook\" again but with more search precision 😉')

    except asyncio.TimeoutError as e:
        print(e)
        await ctx.send(f'{ctx.author.mention}, you took a while to respond... 🤔')

# Answers with a random quote - using quotes.json.
@client.command()
async def quote(ctx):
    with open('quotes.json', 'r') as quotes_file:
        quotes = json.load(quotes_file)
        responses = quotes
        random.seed(a=None)
        response = random.choice(responses)
    await ctx.send(response["text"] + ' - ' + response["author"])



#####   TROUBLESHOOTING AND INFORMATION ########


# Returns information about bot.
@client.command(pass_context=True)
async def info(ctx):
    embed = discord.Embed(colour = discord.Colour.green())
    embed=discord.Embed(title='BookWorm (Bot)', url='https://github.com/Iqrahaq/BookWorm', description='A bot to help contribute to book club activities.', color=0x5ae000)
    embed.set_author(name='Iqra Haq', url='https://www.iqrahaq.com')
    embed.set_thumbnail(url='https://github.com/Iqrahaq/BookWorm/raw/master/vector/bookworm-01.png')
    embed.add_field(name='How to use?', value='Use the "bw!help" command!', inline=False)
    embed.add_field(name='Am I new?', value='Use the "bw!botsetup" command!', inline=False)
    await ctx.send(embed=embed)

# Ping to answer with the ms latency, helpful for troubleshooting.
@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round (client.latency * 1000)}ms ')

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
