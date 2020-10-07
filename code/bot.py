# bot.py

# Include relevant libraries.
import os
import sqlite3
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
CURRENT_BOOK = None
NO_AUTHORS = False
BOOKS_RESULTS = []

intents = discord.Intents.default()
intents.members = True

conn = sqlite3.connect("bookworm.db")
mycursor = conn.cursor()

# Command prefix
client = commands.Bot(command_prefix='bw!', intents=intents)

# Helpful loading prompt.
print("Starting bot...")

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.command(pass_context=True)
async def botsetup(ctx):
    GUILD = ctx.guild.id
    default_role = get(ctx.guild.roles, name="BookWorm")
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS guilds (guild_id int UNIQUE NOT NULL, guild_name text NOT NULL, current_book int NULL, set_by text NULL, deadline text NULL, PRIMARY KEY(guild_id))")
    conn.commit()
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS GUILD_{} (member_id text UNIQUE NOT NULL, guild_id integer NULL, member_name text NOT NULL, member_timezone text NULL, read_status integer DEFAULT '0', member_count integer DEFAULT '0', PRIMARY KEY(member_id), FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)) ".format(
            GUILD))
    conn.commit()
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS BOOKS_{} (book_id text UNIQUE NOT NULL, member_id text NOT NULL, book_isbn int NOT NULL, set_by text NOT NULL, PRIMARY KEY(book_id), FOREIGN KEY (member_id) REFERENCES GUILD_{}(member_id)) ".format(
            GUILD, GUILD))
    conn.commit()
    check_guild_sql = "SELECT guild_id FROM guilds WHERE guild_id=?"
    val = (str(GUILD),)
    mycursor.execute(check_guild_sql, val)
    guild_check = mycursor.fetchone()
    if not guild_check:
        new_guild_sql = "INSERT INTO guilds (guild_id, guild_name) VALUES (?, ?)"
        val = (GUILD, ctx.guild.name,)
        mycursor.execute(new_guild_sql, val)
        conn.commit()

    role = get(ctx.message.guild.roles, name=ROLE)
    if role:
        await ctx.send('Role: "Book Worm" already exists.\nPlease make sure you have this role assigned to join Book Club!')
        for member in ctx.guild.members:
            if role in member.roles:
                check_member_sql = 'SELECT member_id FROM GUILD_{} WHERE member_id=?'.format(ctx.guild.id)
                val = (member.mention,)
                mycursor.execute(check_member_sql, val)
                members_check = mycursor.fetchall()
                if not members_check:
                    new_member_sql = 'INSERT INTO GUILD_{} (member_id, guild_id, member_name, member_id) VALUES (?, ?, ?, ?)'.format(ctx.guild.id)
                    val = (member.mention, ctx.guild.id, member.display_name, member.mention,)
                    mycursor.execute(new_member_sql, val)
                    conn.commit()
            else:
                check_member_sql = 'DELETE FROM GUILD_{} WHERE member_id=?'.format(ctx.guild.id)
                val = (str(member.mention),)
                mycursor.execute(check_member_sql, val)
                conn.commit()

    else:
        await ctx.guild.create_role(name=ROLE, colour=discord.Colour(0x00C09A))
        await ctx.send('Role created: "Book Worm".\nPlease make sure you have this role assigned to join Book Club!')

# Check members in book club.
@client.command(pass_context=True)
async def bookworms(ctx):
    role = get(ctx.message.guild.roles, name=ROLE)
    if role is None:
        await ctx.send('I can\'t find any "Book Worms"!\nAre you sure you have the correct role? Try running "bw!rolesetup".')
    else:
        for member in ctx.guild.members:
            if role in member.roles:
                check_member_sql = 'SELECT member_id FROM GUILD_{} WHERE member_id=?'.format(ctx.guild.id)
                val = (member.mention,)
                mycursor.execute(check_member_sql, val)
                members_check = mycursor.fetchone()
                if not members_check:
                    new_member_sql = 'INSERT INTO GUILD_{} (member_id, guild_id, member_name, member_id) VALUES (?, ?, ?, ?)'.format(ctx.guild.id)
                    val = (member.mention, ctx.guild.id, member.display_name, member.mention,)
                    mycursor.execute(new_member_sql, val)
                    conn.commit()
            else:
                check_member_sql = 'DELETE FROM GUILD_{} WHERE member_id=?'.format(ctx.guild.id)
                val = (str(member.mention),)
                mycursor.execute(check_member_sql, val)
                conn.commit()

        embed = discord.Embed(colour=discord.Colour.green(), title="Book Worms (Book Club Members)")
        mycursor.execute('SELECT member_id, member_name, member_count FROM GUILD_{}'.format(ctx.guild.id))
        all_members = mycursor.fetchall()
        for result in all_members:
            var_member_id = result[0]
            var_member_name = result[1]
            var_member_count = result[2]
            embed.add_field(name='• {}'.format(var_member_name),
					        value='({})\n 📚: {}\n\n'.format(var_member_id, var_member_count), inline=False)
        await ctx.send(embed=embed)


# Picks random book club member.
@client.command()
async def pickaworm(ctx):
    MEMBERS[:] = []
    empty = True
    role = get(ctx.guild.roles, name=ROLE)
    if role is None:
        await ctx.send(
            'I can\'t find any "Book Worms"!\nAre you sure you have the correct role? Try running "bw!rolesetup".')
        return
    else:
        all_members_sql = 'SELECT * FROM GUILD_{}'.format(ctx.guild.id)
        mycursor.execute(all_members_sql)
        all_members = mycursor.fetchall()
        for result in all_members:
            var_member_name = result[2]
            var_member_id = result[0]
            MEMBERS.append('○ {} ({}).\n'.format(var_member_name, var_member_id))
            empty = False

    if empty == True:
        await ctx.send("Nobody has the role \"{}\"!".format(role))

    embed = discord.Embed(colour=discord.Colour.green(), title="Random Book Worm Chosen:")
    random.seed(a=None)
    response = random.choice(MEMBERS)
    embed.description = (response)
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
            embed = discord.Embed(colour=discord.Colour.green(), title="Book Results:")
            i = 1
            while i < book_results_count:
                for book in book_results:
                    if len(book['Authors']) == 0:
                        embed.add_field(name='{}. {} ({})'.format(i, book['Title'], book['Year']),
                                        value='No Authors Specified', inline=False)
                    else:
                        embed.add_field(name='{}. {} ({})'.format(i, book['Title'], book['Year']),
                                        value=', '.join(book['Authors']), inline=False)
                    i += 1
            embed.set_footer(
                text="{} books found!\nCouldn't find the book? Try \"bw!booksearch\" again but with more precision 😉".format(
                    book_results_count))
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
        return message.channel == ctx.channel and message.author == ctx.author and (
            not message.content.startswith("bw!"))

    try:
        current_message = await client.wait_for('message', check=check, timeout=30)
        book_results = goom(current_message.content)
        if book_results:
            book_results_count = len(book_results)
            if book_results_count > 1:
                embed = discord.Embed(colour=discord.Colour.green(), title="Book Results:")
                i = 1
                while i < book_results_count:
                    for book in book_results:
                        if 'ISBN-10' in book:
                            BOOK_CHOICE = book['ISBN-10']
                        elif 'ISBN-13' in book:
                            BOOK_CHOICE = book['ISBN-13']
                        BOOKS_RESULTS.append(BOOK_CHOICE)
                        if len(book['Authors']) == 0:
                            NO_AUTHORS = True
                            embed.add_field(name='{}. {} ({})'.format(i, book['Title'], book['Year']),
                                            value='No Authors Specified', inline=False)
                        else:
                            embed.add_field(name='{}. {} ({})'.format(i, book['Title'], book['Year']),
                                            value=', '.join(book['Authors']), inline=False)
                        i += 1
                embed.set_footer(
                    text="{} books found!\nCouldn't find the book? Try \"bw!setbook\" again but with more precision 😉".format(
                        book_results_count))
                await ctx.send(embed=embed)

                await ctx.send(f'{ctx.author.mention}, what number is it?')

                def check(message):
                    return message.channel == ctx.channel and message.author == ctx.author and (
                        not message.content.startswith("bw!"))

                current_message = await client.wait_for('message', check=check, timeout=30)

            elif book_results_count == 1:
                if 'ISBN-10' in book_results:
                    BOOK_CHOICE = book_results['ISBN-10']
                elif 'ISBN-13' in book_results:
                    BOOK_CHOICE = book_results['ISBN-13']
                BOOKS_RESULTS.append(BOOK_CHOICE)
        else:
            await ctx.send("I couldn't find any books. ¯\\_(ツ)_/¯")

        BOOK_CHOICE = (int(current_message.content) - 1)

        # DB update with new book set
        update_book_sql = "UPDATE guilds SET current_book = ?, set_by = ? WHERE guild_id = ?"
        val = (BOOKS_RESULTS[BOOK_CHOICE], ctx.author.display_name,  ctx.guild.id,)
        mycursor.execute(update_book_sql, val)
        conn.commit()

        update_status_sql = "UPDATE GUILD_{} SET read_status = '0'".format(ctx.guild.id)
        mycursor.execute(update_status_sql)
        conn.commit()

        CURRENT_BOOK = BOOKS_RESULTS[BOOK_CHOICE]

        embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Chosen Book:".format(ctx.author.display_name))
        if meta(CURRENT_BOOK):
            chosen_book = meta(CURRENT_BOOK)
        elif not meta(CURRENT_BOOK):
            chosen_book = meta(CURRENT_BOOK, service='openl')
        else:
            chosen_book = meta(CURRENT_BOOK, service='wiki')

            
        if not ''.join(chosen_book['Authors']) or (len(chosen_book['Authors']) == 0):
            embed.add_field(name='{} ({})'.format(chosen_book['Title'], chosen_book['Year']),
                            value='No Authors Specified', inline=False)
        else:
            embed.add_field(name='{} ({})'.format(chosen_book['Title'], chosen_book['Year']),
                            value=', '.join(chosen_book['Authors']), inline=False)


        if cover(BOOKS_RESULTS[BOOK_CHOICE]):
            thumbnail = cover(str(BOOKS_RESULTS[BOOK_CHOICE]))
            embed.set_thumbnail(url='{}'.format(str(thumbnail['thumbnail'])))
        else:
            embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/no_book_cover.jpg')
        await ctx.send(embed=embed)

    except asyncio.TimeoutError as e:
        print(e)
        await ctx.send(f'{ctx.author.mention}, you took a while to respond... 🤔')


# Set timezone per user.
# @client.command()
# async def settimezone(ctx):

# Add to completed books only if book is set within status.
@client.command()
async def bookfinished(ctx):
    profile_sql = 'SELECT * FROM GUILD_{} WHERE member_id=?'.format(ctx.guild.id)
    val = (ctx.author.mention,)
    mycursor.execute(profile_sql, val)
    current_profile = mycursor.fetchone()
    var_member_id = current_profile[0]
    var_member_name = current_profile[2]
    var_read_status = current_profile[4]
    var_member_count = current_profile[5]

    count_check_sql = 'SELECT current_book, set_by FROM guilds WHERE guild_id=?'
    val = (ctx.guild.id,)
    mycursor.execute(count_check_sql, val)
    result = mycursor.fetchone()
    # if book status is set and book status matches current book then increment.
    var_current_book = (str(result[0]))
    var_set_by = result[1]
    if var_current_book == 'NULL':
        await ctx.send("But there is no set book for the club...? 🤨")
    elif var_read_status == 1:
        await ctx.send("You've already told me that you've finished the set book for the club! 🤪")
    else:
        var_member_count = var_member_count + 1
        update_guild_sql = "UPDATE GUILD_{} SET member_count=?, read_status='1' WHERE member_id=?".format(ctx.guild.id)
        val = (var_member_count, ctx.author.mention,)
        mycursor.execute(update_guild_sql, val)
        conn.commit()

        id = var_current_book + '_' + var_member_id

        update_book_sql = "INSERT INTO BOOKS_{} (book_id, member_id, book_isbn, set_by) VALUES (?, ?, ?, ?)".format(ctx.guild.id)
        val = (id, ctx.author.mention, var_current_book, var_set_by,)
        mycursor.execute(update_book_sql, val)
        conn.commit()

        embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Profile:".format(ctx.author.display_name))
        embed.add_field(name='{}\n(📚: {})'.format(var_member_name, var_member_count), value='{}'.format(var_member_id),
                        inline=False)
        embed.set_footer(text="Well done! You've finished the current set book for the club! 🥳")
        thumbnail = ctx.author.avatar_url
        embed.set_thumbnail(url='{}'.format(thumbnail))
        await ctx.send(embed=embed)


# View bookworm profile.
@client.command()
async def profile(ctx):
    profile_sql = 'SELECT * FROM GUILD_{} WHERE member_id=?'.format(ctx.guild.id)
    val = (ctx.author.mention,)
    mycursor.execute(profile_sql, val)
    current_profile = mycursor.fetchone()
    var_member_name = current_profile[2]
    var_read_status = current_profile[4]
    var_member_count = current_profile[5]
    var_member_id = current_profile[0]

    embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Profile:".format(ctx.author.display_name))
    embed.add_field(name='{}\n(📚: {})'.format(var_member_name, var_member_count), value='{}'.format(var_member_id),
                    inline=False)
    if var_read_status == 1:
        embed.set_footer(text="Well done! You've finished the current set book for the club! 🥳")
    else:
        embed.set_footer(text="It looks like you haven't finished the current set book for the club yet... 🤔")
    thumbnail = ctx.author.avatar_url
    embed.set_thumbnail(url='{}'.format(thumbnail))

    await ctx.send(embed=embed)


# Return current book club reading status.
@client.command()
async def currentbook(ctx):
    current_book_sql = 'SELECT current_book, set_by FROM guilds WHERE guild_id={}'.format(ctx.guild.id)
    mycursor.execute(current_book_sql)
    current_book = mycursor.fetchone()
    CURRENT_BOOK = (str(current_book[0]))
    var_set_by = current_book[1]

    embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Current Read:".format(ctx.guild))
    if CURRENT_BOOK is None:
        embed.add_field(name='There is currently no set book for the book club!', value='\u200b', inline=False)
        embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/bookworm-01.png')
    else:
        if meta(CURRENT_BOOK):
            chosen_book = meta(CURRENT_BOOK)
        elif not meta(CURRENT_BOOK):
            chosen_book = meta(CURRENT_BOOK, service='openl')
        else:
            chosen_book = meta(CURRENT_BOOK, service='wiki')

            
        if not ''.join(chosen_book['Authors']) or (len(chosen_book['Authors']) == 0):
            embed.add_field(name='{} ({})'.format(chosen_book['Title'], chosen_book['Year']),
                            value='No Authors Specified', inline=False)
        else:
            embed.add_field(name='{} ({})'.format(chosen_book['Title'], chosen_book['Year']),
                            value=', '.join(chosen_book['Authors']), inline=False)


        if cover(CURRENT_BOOK):
            thumbnail = cover(str(CURRENT_BOOK))
            embed.set_thumbnail(url='{}'.format(str(thumbnail['thumbnail'])))
        else:
            embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/no_book_cover.jpg')

        embed.set_footer(text="Set by {}. 😉 ".format(var_set_by))
    await ctx.send(embed=embed)

# Returns list of books you've read.
@client.command()
async def mybooks(ctx):
    member_books_sql = 'SELECT book_isbn, set_by FROM BOOKS_{} WHERE member_id=?'.format(ctx.guild.id)
    val = (ctx.author.mention,)
    mycursor.execute(member_books_sql, val)
    results = mycursor.fetchall()

    if results:
        for result in results:
            book = result[0]
            var_set_by = result[1]

            var_count_books = len(results)

            embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Read Books:".format(ctx.author.display_name))
            
            current_book = meta(str(book))
            if len(current_book['Authors']) == 0:
                embed.add_field(name='{} ({})'.format(current_book['Title'], current_book['Year']), value='No Authors Specified',
                                inline=False)
            else:
                embed.add_field(name='{} ({})'.format(current_book['Title'], current_book['Year']),
                                value=', '.join(current_book['Authors']), inline=False)
            
            if 'ISBN-10' in current_book:
                cover_img = current_book['ISBN-10']
            elif 'ISBN-13' in current_book:
                cover_img = current_book['ISBN-13']

            if cover(cover_img):
                thumbnail = cover(cover_img)
                embed.set_thumbnail(url='{}'.format(thumbnail['thumbnail']))
            else:
                embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/no_book_cover.jpg')
            embed.set_footer(
                text="Set by {}.\n{} total books! 😉".format(var_set_by, 
                    var_count_books))
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Read Books:".format(ctx.author.display_name))
        embed.add_field(name='¯\_(ツ)_/¯', value='You haven\'t read any books in this club yet!', inline=False)
        embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/bookworm-01.png')
        await ctx.send(embed=embed)

# Returns list of previously set books.
@client.command()
async def allbooks(ctx):
    all_books_sql = 'SELECT DISTINCT(book_isbn), set_by FROM BOOKS_{}'.format(ctx.guild.id)
    mycursor.execute(all_books_sql)
    results = mycursor.fetchall()
    
    if results:
        for result in results:
            book = result[0]
            var_set_by = result[1]

            var_count_books = len(results)

            embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Read Books:".format(ctx.guild.name))
            current_book = meta(str(book))
            if len(current_book['Authors']) == 0:
                embed.add_field(name='{} ({})'.format(current_book['Title'], current_book['Year']), value='No Authors Specified',
                                inline=False)
            else:
                embed.add_field(name='{} ({})'.format(current_book['Title'], current_book['Year']),
                                value=', '.join(current_book['Authors']), inline=False)
            
            if 'ISBN-10' in current_book:
                cover_img = current_book['ISBN-10']
            elif 'ISBN-13' in current_book:
                cover_img = current_book['ISBN-13']

            if cover(cover_img):
                thumbnail = cover(cover_img)
                embed.set_thumbnail(url='{}'.format(thumbnail['thumbnail']))
            else:
                embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/no_book_cover.jpg')
            embed.set_footer(
                text="Set by {}.\n{} total books! 😉".format(var_set_by, 
                    var_count_books))
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Read Books:".format(ctx.guild.name))
        embed.add_field(name='¯\_(ツ)_/¯', value='No books have been read in this club yet!', inline=False)
        embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/bookworm-01.png')
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
    embed = discord.Embed(colour=discord.Colour.green())
    embed = discord.Embed(title='BookWorm (Bot)', url='https://github.com/Iqrahaq/BookWorm',
                          description='A bot to help contribute to book club activities.', color=0x5ae000)
    embed.set_author(name='Iqra Haq', url='https://www.iqrahaq.com')
    embed.set_thumbnail(url='https://github.com/Iqrahaq/BookWorm/raw/master/img/bookworm-01.png')
    embed.add_field(name='How to use?', value='Use the "bw!help" command!', inline=False)
    embed.add_field(name='Am I new?', value='Use the "bw!botsetup" command!', inline=False)
    await ctx.send(embed=embed)


# Ping to answer with the ms latency, helpful for troubleshooting.
@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms ')


# Error checking...
@client.event
async def on_command_error(ctx, error):
    await ctx.send(f'Error. Try bw!help ({error})')


# Remove default help command to allow for bw!help.
client.remove_command('help')


# Help list and details of commands...
@client.command(pass_context=True)
async def help(ctx):
    embed = discord.Embed(colour=discord.Colour.green())
    embed.set_author(name='Help - List of commands available: ')
    embed.add_field(name='bw!ping', value='Returns my response time in milliseconds.', inline=False)
    embed.add_field(name='bw!info', value='Returns information about me.', inline=False)
    embed.add_field(name='bw!botsetup', value='If I\'m new, use this command to create the required role and entries in my system.', inline=False)
    embed.add_field(name='bw!bookworms', value='Returns a list of the current book club members and their book club information.', inline=False)
    embed.add_field(name='bw!pickaworm', value='Picks a random bookworm (book club member).', inline=False)
    embed.add_field(name='bw!profile', value='Returns your book club profile.', inline=False)
    embed.add_field(name='bw!booksearch', value='Search for a book (Limited to 10 results per search).', inline=False)
    embed.add_field(name='bw!setbook', value='Search for a book (Limited to 10 results per search) and sets it as the current book club\'s read.', inline=False)
    embed.add_field(name='bw!currentbook', value='Check to see what the current set book is for book club.', inline=False)
    embed.add_field(name='bw!bookfinished', value='Let BookWorm Bot know that you\'ve finished the current set book for book club.', inline=False)
    embed.add_field(name='bw!mybooks', value='Returns a list of all the books you\'ve read.', inline=False)
    embed.add_field(name='bw!allbooks', value='Returns a list of all the books that have been read in the club.', inline=False)
    embed.add_field(name='bw!quote', value='Returns an inspirational quote.', inline=False)
    embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/bookworm-01.png')
    embed.set_footer(text="© Iqra Haq (BuraWolf#1158)")
    await ctx.send(embed=embed)


# token
client.run(TOKEN)
