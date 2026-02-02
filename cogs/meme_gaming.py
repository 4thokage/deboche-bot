import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Dict

MEME_API = "https://meme-api.com/gimme/gaming"
from config import GUILD_ID


# =========================
# API CLIENT
# =========================

class MemeClient:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2))

    async def close(self):
        if self.session:
            await self.session.close()

    async def random_meme(self) -> Dict:
        async with self.session.get(MEME_API) as resp:
            if resp.status != 200:
                return {}
            return await resp.json()


# =========================
# EMBED BUILDER
# =========================

def build_meme_embed(data: Dict) -> discord.Embed:
    embed = discord.Embed(
        title=data.get("title", "🎮 Meme de Gaming"),
        color=0x2ecc71,
        url=data.get("postLink")
    )
    if img := data.get("url"):
        embed.set_image(url=img)
    embed.set_footer(text=f"De r/{data.get('subreddit', 'gaming')}")
    return embed


# =========================
# COG
# =========================

class GamingMemes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = MemeClient()

    async def cog_load(self):
        await self.client.start()

    async def cog_unload(self):
        await self.client.close()

    @app_commands.command(
        name="meme_gaming",
        description="Mostrar um meme aleatório de gaming 🕹️",
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def meme(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        data = await self.client.random_meme()
        if not data:
            return await interaction.followup.send("❌ Não consegui encontrar nenhum meme agora.")

        embed = build_meme_embed(data)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(GamingMemes(bot))