import logging
import discord
from discord.ext import commands
from discord import app_commands
from cogwatch import Watcher
from config import GUILD_ID

class DebocheBot(commands.Bot):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.logger = logging.getLogger("DebocheBot")

    async def setup_hook(self):
        # Load Jishaku for debugging
        await self.load_extension("jishaku")

        # Start watcher
        watcher = Watcher(self, path="commands", preload=True, debug=False)
        await watcher.start()

        # Sync commands
        if GUILD_ID:
            await self.tree.sync(guild=discord.Object(id=GUILD_ID))
            self.logger.info(f"Synced slash commands to guild {GUILD_ID}")
        else:
            await self.tree.sync()
            self.logger.info("Synced global slash commands")

    async def on_ready(self):
        self.logger.info(f"Bot ready. Logged in as {self.user}")