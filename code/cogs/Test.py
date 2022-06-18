import os
import json
import random

quotee = ""
selected_source = ""
final_quote = ""

## Get Quote Information
with open(os.path.dirname(__file__) + '/../../quotes_updated.json', 'r') as quotes_file:
    quotes = json.load(quotes_file)
    random.seed(a=None)
    quotee = random.choice(quotes["quoteesArray"])

    if isinstance(quotee["quotes"], dict):
        selected_source = random.choice(list(quotee["quotes"]))
        final_quote = random.choice(quotee["quotes"][selected_source])
    else:
        final_quote = random.choice(quotee["quotes"])

## Assemble Embed
quotee_name = quotee["quotee"]
quotee_profession = quotee["profession"]
quote_image = quotee["image"]

## Find Most Common Used Colour for Embed.
#https://www.geeksforgeeks.org/find-most-used-colors-in-image-using-python/


    
    
