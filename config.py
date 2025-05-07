import discord
import os
import logging


from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE')
}



intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.presences = True

COLOR_CODES = {
    'DEBUG': '\033[94m',
    'INFO': '\033[97m',
    'WARNING': '\033[93m',
    'ERROR': '\033[91m',
    'CRITICAL': '\033[95m',
    'RESET': '\033[0m'
}

class ColorFormatter(logging.Formatter):
    def format(self, record):
        color = COLOR_CODES.get(record.levelname, COLOR_CODES['RESET'])
        message = super().format(record)
        return f"{color}{message}{COLOR_CODES['RESET']}"

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Set custom formatter on the root handler
for handler in logging.getLogger().handlers:
    handler.setFormatter(ColorFormatter('%(levelname)s: %(message)s'))


logging.basicConfig(level=logging.INFO)