import logging
import discord
from discord import Intents
from bot import DebocheBot
from db import Database
from config import TOKEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

intents = Intents.default()
intents.message_content = True
# intents.guilds = True
intents.messages = True

# Instantiate database
db = Database()

# Instantiate bot
bot = DebocheBot(db=db, command_prefix="!", intents=intents)

if __name__ == "__main__":
    bot.run(TOKEN)