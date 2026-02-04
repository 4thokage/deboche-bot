import aiohttp

import discord
from discord import app_commands
from discord.ext import commands
from config import GUILD_ID
KANYE_API = "https://api.kanye.rest/"


class KanyeSays(commands.Cog):
    """Meme: Kanye says..."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_quote(self) -> str:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get(KANYE_API) as resp:
                if resp.status != 200:
                    raise RuntimeError("Kanye API falhou")
                data = await resp.json()
                return data["quote"]

    @commands.hybrid_command(
        name="ye",
        description="Kanye says something profundamente Kanye"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def kanye(self, ctx: commands.Context):
        try:
            quote = await self.fetch_quote()

            embed = discord.Embed(
                description=f"🗣️ **“{quote}”**",
                color=0x000000
            )
            embed.set_author(
                name="Kanye West",
                icon_url="https://upload.wikimedia.org/wikipedia/commons/a/a7/Kanye_West_at_the_2009_Tribeca_Film_Festival.jpg"
            )

            await ctx.send(embed=embed)

        except Exception:
            await ctx.send("❌ Kanye ficou em silêncio. Isto é raro.")


async def setup(bot: commands.Bot):
    await bot.add_cog(KanyeSays(bot))