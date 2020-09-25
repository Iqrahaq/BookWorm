# test.py

# Include relevant libraries.
import os
import random
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Dump file to test different functionality aspects before including them in final bot file.

#Quotes
with open('quotes.json', 'r') as quotes_file:
        quotes = json.load(quotes_file)
        responses = quotes
        random.seed(a=None)
        response = random.choice(responses)
        print (response["text"] + ' - ' + response["author"])