# Member.py

import discord
from discord.ext import commands
from discord.utils import get
import sqlite3
import isbnlib
from isbnlib import *
import asyncio

ROLE = "Book Worm"
conn = sqlite3.connect("bookworm.db")
mycursor = conn.cursor()

class Member(commands.Cog):
    """ a class filled with all commands related to the members. """

    def __init__(self, client):
        self.client = client

    # View bookworm profile.
    @commands.command()
    async def profile(self, ctx):
        profile_sql = 'SELECT member_name, read_status, member_count, member_mention FROM GUILD_{} WHERE member_id=?'.format(ctx.guild.id)
        val = (ctx.author.id,)
        mycursor.execute(profile_sql, val)
        current_profile = mycursor.fetchone()
        var_member_name = current_profile[0]
        var_read_status = current_profile[1]
        var_member_count = current_profile[2]
        var_member_mention = current_profile[3]

        embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Profile:".format(ctx.author.display_name))
        embed.add_field(name='{}\n(📚: {})'.format(var_member_name, var_member_count), value='{}'.format(var_member_mention),
                        inline=False)
        if var_read_status == 1:
            embed.set_footer(text="Well done! You've finished the current set book for the club! 🥳")
        else:
            embed.set_footer(text="It looks like you haven't finished the current set book for the club yet... 🤔")
        thumbnail = ctx.author.avatar_url
        embed.set_thumbnail(url='{}'.format(thumbnail))

        await ctx.send(embed=embed)


    # Add to completed books only if book is set within status.
    @commands.command()
    async def bookfinished(self, ctx):
        profile_sql = 'SELECT member_mention, member_name, read_status, member_count, member_id FROM GUILD_{} WHERE member_id=?'.format(ctx.guild.id)
        val = (ctx.author.id,)
        mycursor.execute(profile_sql, val)
        current_profile = mycursor.fetchone()
        var_member_mention = current_profile[0]
        var_member_name = current_profile[1]
        var_read_status = current_profile[2]
        var_member_count = current_profile[3]
        var_member_id = current_profile[4]

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
            val = (var_member_count, ctx.author.id,)
            mycursor.execute(update_guild_sql, val)
            conn.commit()

            id = var_current_book + '_' + var_member_id

            update_book_sql = "INSERT INTO BOOKS_{} (book_id, member_id, book_isbn, set_by) VALUES (?, ?, ?, ?)".format(ctx.guild.id)
            val = (id, ctx.author.id, var_current_book, var_set_by,)
            mycursor.execute(update_book_sql, val)
            conn.commit()

            embed = discord.Embed(colour=discord.Colour.green(), title="{}'s Profile:".format(ctx.author.display_name))
            embed.add_field(name='{}\n(📚: {})'.format(var_member_name, var_member_count), value='{}'.format(var_member_mention),
                            inline=False)
            embed.set_footer(text="Well done! You've finished the current set book for the club! 🥳")
            thumbnail = ctx.author.avatar_url
            embed.set_thumbnail(url='{}'.format(thumbnail))
            await ctx.send(embed=embed)

    # Returns list of books you've read.
    @commands.command()
    async def mybooks(self, ctx):
        member_books_sql = 'SELECT book_isbn, set_by FROM BOOKS_{} WHERE member_id=?'.format(ctx.guild.id)
        val = (ctx.author.id,)
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

def setup(client):
    client.add_cog(Member(client))

