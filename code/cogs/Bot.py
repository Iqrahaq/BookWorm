# Bot.py

import discord
from discord.ext import commands
from discord.utils import get
import os
import mysql.connector
import isbnlib
from isbnlib import *
import random
import json
import asyncio

ROLE = "Book Worm"

class Bot(commands.Cog):
    """ a class filled with all commands related to the bot. """

    def __init__(self, client):
        self.client = client
        self.connection = None
    
    def initdb():
        return mysql.connector.connect(
            host = os.getenv('HOST'),
            user = os.getenv('USER'),
            password = os.getenv('PASSWORD'),
            database = os.getenv('DATABASE')
        )

    def dbcursor():
        try:
            self.connection.ping(reconnect=True, attempts=3, delay=5)
        except mysql.connector.Error as err:
            self.connection = initdb()
        return self.connection.cursor()

    # First command to be run before all other commands (to help with setting up DB and Role).
    @commands.command()
    async def botsetup(self, ctx):
        mycursor = dbcursor()
        GUILD = ctx.guild.id
        default_role = get(ctx.guild.roles, name="BookWorm")
        mycursor.execute("SET NAMES utf8mb4;")
        self.connection.commit()
        mycursor.execute(
            "CREATE TABLE IF NOT EXISTS guilds (guild_id VARCHAR(50) UNIQUE NOT NULL, guild_name VARCHAR(255) NOT NULL, current_book VARCHAR(50) NULL, set_by VARCHAR(255) NULL, deadline VARCHAR(255) NULL, PRIMARY KEY(guild_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;")
        self.connection.commit()
        mycursor.execute(
            "CREATE TABLE IF NOT EXISTS GUILD_{} (member_id VARCHAR(255) UNIQUE NOT NULL, guild_id VARCHAR(50) NULL, member_name VARCHAR(255) NOT NULL, member_mention VARCHAR(255) NOT NULL, member_timezone VARCHAR(255) NULL, read_status VARCHAR(50) DEFAULT '0', member_count VARCHAR(50) DEFAULT '0', PRIMARY KEY(member_id), FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;".format(GUILD))
        self.connection.commit()
        mycursor.execute(
            "CREATE TABLE IF NOT EXISTS BOOKS_{} (book_id VARCHAR(255) UNIQUE NOT NULL, member_id VARCHAR(255) NOT NULL, book_isbn VARCHAR(50) NOT NULL, set_by VARCHAR(255) NOT NULL, PRIMARY KEY(book_id), FOREIGN KEY (member_id) REFERENCES GUILD_{}(member_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;".format(GUILD, GUILD))
        self.connection.commit()
        check_guild_sql = "SELECT guild_id FROM guilds WHERE guild_id=%s;"
        val = (str(GUILD),)
        mycursor.execute(check_guild_sql, val)
        guild_check = mycursor.fetchone()
        if not guild_check:
            new_guild_sql = "INSERT INTO guilds (guild_id, guild_name) VALUES (%s, %s);"
            val = (GUILD, ctx.guild.name,)
            mycursor.execute(new_guild_sql, val)
            self.connection.commit()

        role = get(ctx.message.guild.roles, name=ROLE)
        if role:
            await ctx.send('Role: "Book Worm" already exists.\nPlease make sure you have this role assigned to join Book Club!')
            for member in ctx.guild.members:
                if role in member.roles:
                    check_member_sql = 'SELECT member_id FROM GUILD_{} WHERE member_id=%s;'.format(ctx.guild.id)
                    val = (member.id,)
                    mycursor.execute(check_member_sql, val)
                    members_check = mycursor.fetchall()
                    if not members_check:
                        new_member_sql = 'INSERT INTO GUILD_{} (member_id, guild_id, member_name, member_mention) VALUES (%s, %s, %s, %s);'.format(ctx.guild.id)
                        val = (member.id, ctx.guild.id, member.display_name, member.mention,)
                        mycursor.execute(new_member_sql, val)
                        self.connection.commit()
                    else:
                        update_member_sql = 'UPDATE GUILD_{} SET member_name=%s, member_mention=%s WHERE member_id=%s;'.format(ctx.guild.id)
                        val = (member.display_name, member.mention, member.id, )
                        mycursor.execute(update_member_sql, val)
                        self.connection.commit()
                else:
                    check_member_sql = 'DELETE FROM GUILD_{} WHERE member_id=%s;'.format(ctx.guild.id)
                    val = (str(member.id),)
                    mycursor.execute(check_member_sql, val)
                    self.connection.commit()

        else:
            await ctx.guild.create_role(name=ROLE, colour=discord.Colour(0x00C09A))
            await ctx.send('Role created: "Book Worm".\nPlease make sure you have this role assigned to join Book Club!')

        
    # Searches for books (generic search that is similar to setbook).
    @commands.command()
    async def booksearch(self, ctx):
        await ctx.send(f'{ctx.author.mention}, what\'s the book called?')

        def check(message):
            return message.channel == ctx.channel

        try:
            current_message = await self.client.wait_for('message', check=check, timeout=30)
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
                    text="{} books found!\nCouldn't find the book? Try again but with more precision 😉".format(
                        book_results_count))
                await ctx.send(embed=embed)
            else:
                await ctx.send("I couldn't find any books. ¯\\_(ツ)_/¯")
        except asyncio.TimeoutError as e:
            print(e)
            await ctx.send("Response timed out.")


    # Answers with a random quote - using quotes.json.
    @commands.command()
    async def quote(self, ctx):
        with open(os.path.dirname(__file__) + '/../../quotes.json', 'r') as quotes_file:
            quotes = json.load(quotes_file)
            responses = quotes
            random.seed(a=None)
            response = random.choice(responses)
        await ctx.send(response["text"] + ' - ' + response["author"])

        
    #######   TROUBLESHOOTING AND INFORMATION ########


    # Returns information about bot.
    @commands.command()
    async def info(self, ctx):
        embed = discord.Embed(colour=discord.Colour.green())
        embed = discord.Embed(title='BookWorm (Bot)', url='https://github.com/Iqrahaq/BookWorm',
                                description='A bot to help contribute to book club activities.', color=0x5ae000)
        embed.set_author(name='Iqra Haq', url='https://www.iqrahaq.com')
        embed.set_thumbnail(url='https://github.com/Iqrahaq/BookWorm/raw/master/img/bookworm-01.png')
        embed.add_field(name='How to use?', value='Use the "bw!help" command!', inline=False)
        embed.add_field(name='Am I new?', value='Use the "bw!botsetup" command!', inline=False)
        await ctx.send(embed=embed)
        


    # Ping to answer with the ms latency, helpful for troubleshooting.
    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'Pong! {round(self.client.latency * 1000)}ms ')



    # Help list and details of commands...
    @commands.command(pass_context=True)
    async def help(self, ctx):
        embed = discord.Embed(colour=discord.Colour.green())
        embed.set_author(name='Help - List of commands available: ')
        embed.add_field(name='bw!ping', value='Returns my response time in milliseconds.', inline=False)
        embed.add_field(name='bw!info', value='Returns information about me.', inline=False)
        embed.add_field(name='bw!botsetup', value='If I\'m new, use this command to create the required role and entries in my system.', inline=False)
        embed.add_field(name='bw!bookworms', value='Lists the current book club members and their book club information.', inline=False)
        embed.add_field(name='bw!topfive', value='Lists the top 5 book worms (book club members).', inline=False)
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


def setup(client):
    client.add_cog(Bot(client))


