# bot.py

# Include relevant libraries.
import os
import pymysql
from pymysql import cursors
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

# DB connectivity
mydb = pymysql.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    db=os.getenv('DB_DATABASE')
)

mycursor = mydb.cursor()

# Command prefix
client = commands.Bot(command_prefix='bw!')

# Helpful loading prompt.
print("Starting bot...")


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.command()
async def botsetup(ctx):
    GUILD = ctx.guild.id
    default_role = get(ctx.guild.roles, name="BookWorm")
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS GUILD_{} (member_id INT(100) NOT NULL AUTO_INCREMENT, guild_id VARCHAR(100) DEFAULT NULL, member_name VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL, member_tag VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL, member_timezone VARCHAR(10) DEFAULT NULL, read_status BOOLEAN DEFAULT '0', member_count INT(5) DEFAULT '0', member_books VARCHAR(1000) DEFAULT NULL, PRIMARY KEY(member_id)) ".format(
            GUILD))
    mydb.commit()
    mycursor.execute("SELECT * FROM guilds WHERE guild_id=%s", (str(GUILD)))
    guilds_check = mycursor.fetchone()
    if not guilds_check:
        new_guild_sql = 'INSERT INTO guilds (guild_id, guild_name) VALUES (%s, %s)'
        val = (str(GUILD), str(ctx.guild.name))
        mycursor.execute(new_guild_sql, val)
        mydb.commit()

    if get(ctx.guild.roles, name=ROLE):
        await ctx.send(
            'Role: "Book Worm" already exists.\nPlease make sure you have this role assigned to join Book Club!')
    else:
        await ctx.guild.create_role(name=ROLE, colour=discord.Colour(0x00C09A))
        await ctx.send('Role created: "Book Worm".\nPlease make sure you have this role assigned to join Book Club!')


# Check members in book club.
@client.command(pass_context=True)
async def bookworms(ctx):
    role = get(ctx.guild.roles, name=ROLE)
    if role is None:
        await ctx.send(
            'I can\'t find any "Book Worms"!\nAre you sure you have the correct role? Try running "bw!rolesetup".')
        return
    else:
        for member in ctx.guild.members:
            check_member_sql = 'SELECT * FROM GUILD_{} WHERE member_tag=%s'.format(ctx.guild.id)
            val = (str(member.mention))
            mycursor.execute(check_member_sql, val)
            members_check = mycursor.fetchall()
            if role in member.roles:
                if not members_check:
                    new_member_sql = 'INSERT INTO GUILD_{} (guild_id, member_name, member_tag) VALUES (%s, %s, %s)'.format(
                        ctx.guild.id)
                    val = (str(ctx.guild.id), str(member.display_name), str(member.mention))
                    mycursor.execute(new_member_sql, val)
                    mydb.commit()
            else:
                check_member_sql = 'DELETE FROM GUILD_{} WHERE member_tag=%s'.format(ctx.guild.id)
                val = (str(member.mention))
                mycursor.execute(check_member_sql, val)
                mydb.commit()

    embed = discord.Embed(colour=discord.Colour.green(), title="Book Worms (Book Club Members)")
    all_members_sql = 'SELECT * FROM GUILD_{}'.format(ctx.guild.id)
    mycursor.execute(all_members_sql)
    all_members = mycursor.fetchall()
    for result in all_members:
        var_member_name = result[2]
        var_member_tag = result[3]
        var_member_count = result[5]
        embed.add_field(name='• {}'.format(var_member_name),
                        value='({})\n 📚: {}\n\n'.format(var_member_tag, var_member_count), inline=False)
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
            var_member_tag = result[3]
            MEMBERS.append('○ {} ({}).\n'.format(var_member_name, var_member_tag))
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
        update_book_sql = "UPDATE guilds SET current_book = %s, set_by = %s WHERE guild_id = %s"
        val = (str(BOOKS_RESULTS[BOOK_CHOICE]), str(ctx.author.display_name),  str(ctx.guild.id))
        mycursor.execute(update_book_sql, val)
        mydb.commit()

        update_status_sql = "UPDATE GUILD_{} SET read_status = '0'".format(ctx.guild.id)
        mycursor.execute(update_status_sql)
        mydb.commit()

        CURRENT_BOOK = str(BOOKS_RESULTS[BOOK_CHOICE])

        embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Chosen Book:".format(ctx.author.display_name))
        if not meta(CURRENT_BOOK):
            chosen_book = meta(CURRENT_BOOK, service='openl')
        else:
            chosen_book = meta(CURRENT_BOOK)


        if len(chosen_book['Authors']) == 0:
            embed.add_field(name='{} ({})'.format(chosen_book['Title'], chosen_book['Year']),
                            value='No Authors Specified', inline=False)
        else:
            embed.add_field(name='{} ({})'.format(chosen_book['Title'], chosen_book['Year']),
                            value=', '.join(chosen_book['Authors']), inline=False)


        if cover(BOOKS_RESULTS[BOOK_CHOICE]):
            thumbnail = cover(BOOKS_RESULTS[BOOK_CHOICE])
            embed.set_thumbnail(url='{}'.format(thumbnail['thumbnail']))
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
    profile_sql = 'SELECT * FROM GUILD_{} WHERE member_tag=%s'.format(ctx.guild.id)
    val = (str(ctx.author.mention))
    mycursor.execute(profile_sql, val)
    current_profile = mycursor.fetchone()
    var_member_name = current_profile[2]
    var_read_status = current_profile[5]
    var_member_count = current_profile[6]
    var_member_tag = current_profile[3]

    count_check_sql = 'SELECT current_book FROM guilds WHERE guild_id=%s'
    val = (str(ctx.guild.id))
    mycursor.execute(count_check_sql, val)
    result = mycursor.fetchone()
    # if book status is set and book status matches current book then increment.
    print(result)
    if result == 'NULL':
        await ctx.send("But there is no set book for the club...? 🤨")
    elif var_read_status == 1:
        await ctx.send("You've already told me that you've finished the set book for the club! 🤪")
    else:
        var_member_count = var_member_count + 1
        update_sql = "UPDATE GUILD_{} SET member_count=%s, read_status='1' WHERE member_tag=%s".format(ctx.guild.id)
        val = (var_member_count, str(ctx.author.mention))
        mycursor.execute(update_sql, val)
        mydb.commit()

        embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Profile:".format(ctx.author.display_name))
        embed.add_field(name='{}\n(📚: {})'.format(var_member_name, var_member_count), value='{}'.format(var_member_tag),
                        inline=False)
        embed.set_footer(text="Well done! You've finished the current set book for the club! 🥳")
        thumbnail = ctx.author.avatar_url
        embed.set_thumbnail(url='{}'.format(thumbnail))
        await ctx.send(embed=embed)


# View bookworm profile.
@client.command()
async def profile(ctx):
    profile_sql = 'SELECT * FROM GUILD_{} WHERE member_tag=%s'.format(ctx.guild.id)
    val = (str(ctx.author.mention))
    mycursor.execute(profile_sql, val)
    current_profile = mycursor.fetchone()
    var_member_name = current_profile[2]
    var_read_status = current_profile[5]
    var_member_count = current_profile[6]
    var_member_tag = current_profile[3]

    embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Profile:".format(ctx.author.display_name))
    embed.add_field(name='{}\n(📚: {})'.format(var_member_name, var_member_count), value='{}'.format(var_member_tag),
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
    var_current_book = current_book[0]
    var_set_by = current_book[1]

    embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Current Read:".format(ctx.guild))
    if var_current_book is None:
        embed.add_field(name='There is currently no set book for the book club!', value='\u200b', inline=False)
        embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/bookworm-01.png')
    else:
        CHOSEN_BOOK = meta(str(var_current_book))
        if len(CHOSEN_BOOK['Authors']) == 0:
            embed.add_field(name='{} ({})'.format(CHOSEN_BOOK['Title'], CHOSEN_BOOK['Year']), value='No Authors Specified',
                            inline=False)
        else:
            embed.add_field(name='{} ({})'.format(CHOSEN_BOOK['Title'], CHOSEN_BOOK['Year']),
                            value=', '.join(CHOSEN_BOOK['Authors']), inline=False)
        thumbnail = cover(var_current_book)
        embed.set_thumbnail(url='{}'.format(thumbnail['thumbnail']))

    embed.set_footer(text="Set by {}. 😉 ".format(var_set_by))
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
    embed.add_field(name='bw!quote', value='Returns an inspirational quote.', inline=False)
    embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/bookworm-01.png')
    embed.set_footer(text="© Iqra Haq (BuraWolf#1158)")
    await ctx.send(embed=embed)


# token
client.run(TOKEN)
