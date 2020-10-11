# Guild.py

import discord
from discord.ext import commands
from discord.utils import get
import sqlite3
import isbnlib
from isbnlib import *
import asyncio


ROLE = "Book Worm"
MEMBERS = []
CURRENT_BOOK = None
NO_AUTHORS = False
BOOKS_RESULTS = []
conn = sqlite3.connect("bookworm.db")
mycursor = conn.cursor()

class Guild(commands.Cog):
    """ a class filled with all commands related to the guild. """

    def __init__(self, client):
        self.client = client

    # Check members in book club.
    @commands.command()
    async def bookworms(self, ctx):
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

            embed = discord.Embed(colour=discord.Colour.green(), title="Book Worms")
            mycursor.execute('SELECT member_id, member_name, member_count FROM GUILD_{}'.format(ctx.guild.id))
            all_members = mycursor.fetchall()
            for result in all_members:
                var_member_id = result[0]
                var_member_name = result[1]
                var_member_count = result[2]
                embed.add_field(name='• {}'.format(var_member_name),
					            value='({})\n 📚: {}\n\n'.format(var_member_id, var_member_count), inline=False)
            embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/bookworm-01.png')
            await ctx.send(embed=embed)

    # Retrieves top 5 members.
    @commands.command()
    async def topfive(self, ctx):
        embed = discord.Embed(colour=discord.Colour.green(), title="TOP 5 Book Worms")
        mycursor.execute('SELECT member_id, member_name, member_count FROM GUILD_{} ORDER BY member_count DESC LIMIT 5'.format(ctx.guild.id))
        all_members = mycursor.fetchall()
        n = 1
        for result in all_members:
            var_member_id = result[0]
            var_member_name = result[1]
            var_member_count = result[2]
            embed.add_field(name='{0}• {1}'.format(n, var_member_name),
                            value='({})\n 📚: {}\n\n'.format(var_member_id, var_member_count), inline=False)
            n = n + 1
        embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/bookworm-01.png')
        await ctx.send(embed=embed)
        n = 1


    # Picks random book club member.
    @commands.command()
    async def pickaworm(self, ctx):
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
        embed.set_thumbnail(url='https://raw.githubusercontent.com/Iqrahaq/BookWorm/master/img/bookworm-01.png')
        await ctx.send(embed=embed)


    # Set a book for the book club.
    @commands.command()
    async def setbook(self, ctx):
        BOOKS_RESULTS[:] = []
        await ctx.send(f'{ctx.author.mention}, what\'s the book called?')

        def check(message):
            return message.channel == ctx.channel and message.author == ctx.author and (
                not message.content.startswith("bw!"))

        try:
            current_message = await self.client.wait_for('message', check=check, timeout=30)
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

                    current_message = await self.client.wait_for('message', check=check, timeout=30)

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


    # Return current book club reading status.
    @commands.command()
    async def currentbook(self, ctx):
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

    # Returns list of previously set books.
    @commands.command()
    async def allbooks(self, ctx):
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


def setup(client):
    client.add_cog(Guild(client))