import os
import discord
import mysql.connector
import logging
#from dotenv import load_dotenv


from config import DB_CONFIG, intents
from config import TOKEN
from commands import register_commands
from events import register_events

client = discord.Client(intents = intents)
tree = discord.app_commands.CommandTree(client)

register_commands(tree)
register_events(client, tree)


client.run(TOKEN)

