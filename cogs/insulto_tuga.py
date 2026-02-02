import os
import aiohttp

import discord
from discord import app_commands
from discord.ext import commands
from config import GUILD_ID

EVIL_INSULT_API = "https://evilinsult.com/generate_insult.php?lang=pt&type=json"


class InsultoTuga(commands.Cog):
    """Insultos à tuga via API (sem chorar)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_insulto(self) -> str:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(EVIL_INSULT_API) as resp:
                    if resp.status != 200:
                        raise RuntimeError("API não respondeu 200")

                    data = await resp.json()
                    return data.get("insult", "Hoje não há insultos, só desilusão.")
        except Exception:
            return "A API falhou… tal como tu nesse jogo."

    @app_commands.command(
        name="insulto_tuga",
        description="Recebe um insulto à tuga (sem chorar)"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def insulto_tuga(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        insulto = await self.fetch_insulto()

        embed = discord.Embed(
            title="🇵🇹 Insulto Tuga",
            description=insulto,
            color=0xE10600
        )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(InsultoTuga(bot))