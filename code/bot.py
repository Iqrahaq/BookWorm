# bot.py

# Include relevant libraries.
import os
import mysql.connector
from mysql.connector import Error
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
BOOKS_RESULTS = []

#DB connectivity
def create_connection():
	conn = None
	try:
		conn = mysql.connector.connect(
			host=os.getenv('DB_HOST'),
			user=os.getenv('DB_USER'),
			password=os.getenv('DB_PASSWORD'),
			database=os.getenv('DB_DATABASE')
		)
		print ("Connection to MySQL DB successful")
	except Error as e:
		print(f"The error '{e}' occured.")

	return conn

#Open DB Connection
conn = create_connection()
mycursor = conn.cursor(buffered=True)

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
	mycursor.execute("USE {}".format(conn.database))
	mycursor.execute('SHOW TABLES')
	all_tables = mycursor.fetchall()
	for table in all_tables:
		if table is not GUILD or all_tables is empty:
			mycursor.execute("CREATE TABLE IF NOT EXISTS GUILD_{} (member_id INT(100) NOT NULL AUTO_INCREMENT, guild_id VARCHAR(100) DEFAULT NULL, member_name VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL, member_tag VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL, member_timezone VARCHAR(10) DEFAULT NULL, member_count INT(5) DEFAULT '0', member_books VARCHAR(1000) DEFAULT NULL, member_status BOOLEAN DEFAULT NULL, PRIMARY KEY(member_id)) ".format(GUILD))
			conn.commit()
			val = (ctx.guild.id,)
			mycursor.execute("SELECT * FROM guilds WHERE guild_id=%s", val)
			guilds_check = mycursor.fetchone()
			if not guilds_check:
				val = (str(GUILD), str(ctx.guild.name),)
				mycursor.execute("INSERT INTO guilds (guild_id, guild_name) VALUES (%s, %s)", val)				
				conn.commit()
	
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
			val = (ctx.guild.id, str(member.mention),)
			mycursor.execute("SELECT * FROM GUILD_%s WHERE member_tag=%s", val)
			members_check = mycursor.fetchall()
			if role in member.roles:
				if not members_check:
					val = (ctx.guild.id, str(ctx.guild.id), str(member), str(member.mention),)
					mycursor.execute("INSERT INTO GUILD_%s (guild_id, member_name, member_tag) VALUES (%s, %s, %s)", val)
					conn.commit()
					empty = False
				else:
					empty = False
			else:
				val = (ctx.guild.id, str(member.mention),)
				mycursor.execute("DELETE FROM GUILD_%s WHERE member_tag=%s", val)
				conn.commit()
	if empty == True:
		await ctx.send("Nobody has the role \"{}\"!".format(role))

	embed = discord.Embed(colour = discord.Colour.green(), title="Book Worms (Book Club Members)")
	val = (ctx.guild.id,)
	mycursor.execute("SELECT * FROM GUILD_%s", val)
	all_members = mycursor.fetchall()
	for result in all_members:
		var_member_name = result[2].decode()
		var_member_tag = result[3].decode()
		var_member_count = result[5]
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
		val = (str(ctx.guild.id),)
		mycursor.execute("SELECT * FROM GUILD_%s", val)
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
					if len(book['Authors']) == 0:
						embed.add_field(name='{}. {} ({})'.format(i, book['Title'], book['Year']), value='No Authors Specified', inline=False)
					else:
						embed.add_field(name='{}. {} ({})'.format(i, book['Title'], book['Year']), value=', '.join(book['Authors']), inline=False)
					i+=1
			embed.set_footer(text="{} books found!\nCouldn't find the book? Try \"bw!booksearch\" again but with more precision 😉".format(book_results_count))
			await ctx.send(embed=embed)
		else:
			await ctx.send("I couldn't find any books. ¯\\_(ツ)_/¯")
	except asyncio.TimeoutError as e:
		print(e)
		await ctx.send("Response timed out.")

# Set a book for the book club.
@client.command()
async def setbook(ctx):
	BOOKS_RESULTS[:] = []
	await ctx.send(f'{ctx.author.mention}, what\'s the book called?')
	def check(message):
		return message.channel == ctx.channel and message.author == ctx.author and (not message.content.startswith("bw!"))
	try:
		current_message = await client.wait_for('message', check=check, timeout=30)
		book_results = goom(current_message.content)
		if book_results:
			book_results_count = len(book_results)
			if(book_results_count > 1):
				embed = discord.Embed(colour = discord.Colour.green(), title="Book Results:")
				i = 1
				while i < book_results_count:
					for book in book_results:
						if 'ISBN-10' in book:
							BOOK_CHOICE = book['ISBN-10']
						elif 'ISBN-13' in book:
							BOOK_CHOICE = book['ISBN-13']
						BOOKS_RESULTS.append(BOOK_CHOICE)
						if len(book['Authors']) == 0:
							embed.add_field(name='{}. {} ({})'.format(i, book['Title'], book['Year']), value='No Authors Specified', inline=False)
						else:
							embed.add_field(name='{}. {} ({})'.format(i, book['Title'], book['Year']), value=', '.join(book['Authors']), inline=False)
						i+=1
				embed.set_footer(text="{} books found!\nCouldn't find the book? Try \"bw!setbook\" again but with more precision 😉".format(book_results_count))
				await ctx.send(embed=embed)

				await ctx.send(f'{ctx.author.mention}, what number is it?')
				def check(message):
					return message.channel == ctx.channel and message.author == ctx.author and (not message.content.startswith("bw!"))
				current_message = await client.wait_for('message', check=check, timeout=30)

			elif book_results_count == 1:
				if 'ISBN-10' in book:
					BOOK_CHOICE = book['ISBN-10']
				elif 'ISBN-13' in book:
					BOOK_CHOICE = book['ISBN-13']
				BOOKS_RESULTS.append(BOOK_CHOICE)
		else:
			await ctx.send("I couldn't find any books. ¯\\_(ツ)_/¯")

		BOOK_CHOICE = (int(current_message.content)-1)

		# DB update with new book set
		val = (str(BOOKS_RESULTS[BOOK_CHOICE]), str(ctx.author.name), str(ctx.guild.id),)
		mycursor.execute("UPDATE guilds SET current_book = %s, set_by = %s WHERE guild_id = %s", val)
		conn.commit()

		embed = discord.Embed(colour = discord.Colour.green(), title="{}'s Chosen Book:".format(ctx.author))
		CHOSEN_BOOK = meta(BOOKS_RESULTS[BOOK_CHOICE])
		if len(CHOSEN_BOOK['Authors']) == 0:
			embed.add_field(name='{} ({})'.format(CHOSEN_BOOK['Title'], CHOSEN_BOOK['Year']), value='No Authors Specified', inline=False)
		else:
			embed.add_field(name='{} ({})'.format(CHOSEN_BOOK['Title'], CHOSEN_BOOK['Year']), value=', '.join(CHOSEN_BOOK['Authors']), inline=False)
		thumbnail = cover(BOOKS_RESULTS[BOOK_CHOICE])
		embed.set_thumbnail(url='{}'.format(thumbnail['thumbnail']))
		embed.set_footer(text="This book has been set as the current club read 😊".format(book_results_count))
		await ctx.send(embed=embed)
		await embed.pin()
		
	except asyncio.TimeoutError as e:
		print(e)
		await ctx.send(f'{ctx.author.mention}, you took a while to respond... 🤔')
	

# Set timezone per user.
# @client.command()
# async def settimezone(ctx):

# View club stats.

# View bookworm profile.
@client.command(pass_context=True)
async def profile(ctx):
	val = ((ctx.guild.id), str(ctx.author.mention),)
	mycursor.execute("SELECT * FROM GUILD_%s WHERE member_tag=%s", val)
	result = mycursor.fetchone()
	var_member_name = result[2].decode()
	var_member_tag = result[3].decode()
	var_member_timezone = result[4]
	var_member_count = result[5]
	embed = discord.Embed(colour = discord.Colour.green(), title="{}'s Profile:".format(ctx.author.name), description='{}'.format(var_member_tag))
	embed.add_field(name='📚\t{}\n🌍\t({})'.format(var_member_count, var_member_timezone), value='\u200b', inline=True)
	thumbnail = ctx.author.avatar_url
	embed.set_thumbnail(url='{}'.format(thumbnail))
	await ctx.send(embed=embed)


# Return current book club reading status.
@client.command()
async def status(ctx):
	val = (str(ctx.guild.id),)
	mycursor.execute("SELECT * FROM guilds WHERE guild_id=%s", val)
	result = mycursor.fetchone()
	current_book = result[3]
	set_by = result[4]
	embed = discord.Embed(colour = discord.Colour.green(), title="{}'s Current Read:".format(ctx.guild))
	CHOSEN_BOOK = meta(current_book)
	if len(CHOSEN_BOOK['Authors']) == 0:
		embed.add_field(name='{} ({})'.format(CHOSEN_BOOK['Title'], CHOSEN_BOOK['Year']), value='No Authors Specified', inline=False)
	else:
		embed.add_field(name='{} ({})'.format(CHOSEN_BOOK['Title'], CHOSEN_BOOK['Year']), value=', '.join(CHOSEN_BOOK['Authors']), inline=False)
	thumbnail = cover(current_book)
	embed.set_thumbnail(url='{}'.format(thumbnail['thumbnail']))
	embed.set_footer(text="Set by: {}".format(set_by))
	await ctx.send(embed=embed)
	


# Answers with a random quote - using quotes.json.
@client.command()
async def quote(ctx):
	with open('quotes.json', 'r') as quotes_file:
		quotes = json.load(quotes_file)
		responses = quotes
		random.seed(a=None)
		response = random.choice(responses)
	await ctx.send(response["text"] + ' - ' + response["author"])

#######   TROUBLESHOOTING AND INFORMATION ########


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
	embed.add_field(name='bw!booksearch', value='Search for a book (Limited to 10 results per search).', inline=False)
	embed.add_field(name='bw!setbook', value='Search for a book (Limited to 10 results per search).', inline=False)
	embed.add_field(name='bw!quote', value='Returns an inspirational quote.', inline=False)
	await ctx.send(embed=embed)

#token
client.run(TOKEN)
