import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Context
import aiohttp
from datetime import datetime
from config import GUILD_ID
from paginator import EmbedPaginator


IPMA_WARNINGS_URL = "https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json"
IPMA_AREAS_URL = "https://api.ipma.pt/open-data/distrits-islands.json"


WARNING_COLORS = {
    "yellow": 0xF1C40F,
    "orange": 0xE67E22,
    "red": 0xE74C3C,
    "green": 0x2ECC71,
}


def format_ipma_warnings(warnings: list, areas: dict) -> str:
    blocks = []

    for w in warnings:
        level = w["awarenessLevelID"].upper()
        local = areas.get(w["idAreaAviso"], w["idAreaAviso"])

        start = datetime.fromisoformat(w["startTime"])
        end = datetime.fromisoformat(w["endTime"])

        block = (
            f"⚠️ **{local}**\n"
            f"• **Nível:** {level}\n"
            f"• **Tipo:** {w['awarenessTypeName']}\n"
            f"• **Período:** {start:%d/%m %H:%M} → {end:%d/%m %H:%M}\n"
        )

        if w.get("text"):
            block += f"• **Descrição:** {w['text']}\n"

        blocks.append(block)

    return "\n".join(blocks)


class IPMA(commands.Cog):
    """Avisos meteorológicos do IPMA (Portugal)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, "session"):
            self.bot.session = aiohttp.ClientSession()
            

    async def fetch_areas(self) -> dict:
        """Retorna um mapa idAreaAviso -> Local"""
        async with self.bot.session.get(IPMA_AREAS_URL, ssl=False) as r:
            data = await r.json()

        return {
            item["idAreaAviso"]: item["local"]
            for item in data.get("data", [])
        }

    @commands.hybrid_command(
        name="ipma",
        description="Mostra avisos meteorológicos ativos do IPMA"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ipma(self, ctx: Context):
        await ctx.defer()

        try:
            async with self.bot.session.get(IPMA_WARNINGS_URL, ssl=False) as r:
                if r.status != 200:
                    raise Exception("Erro ao contactar IPMA")
                warnings = await r.json()

            areas = await self.fetch_areas()

            # Filtrar apenas avisos ativos (≠ green)
            active = [w for w in warnings if w["awarenessLevelID"] != "green"]

            if not active:
                embed = discord.Embed(
                    title="🌤️ IPMA",
                    description="Sem avisos meteorológicos ativos.",
                    color=0x2ECC71
                )
                await interaction.followup.send(embed=embed)
                return

            text = format_ipma_warnings(active, areas)

            paginator = EmbedPaginator(
                text=text,
                title="⚠️ Avisos Meteorológicos IPMA",
                color=0xE67E22,
                chunk_size=3800  # margem de segurança
            )

            await paginator.start(ctx)

        except Exception as e:
            await ctx.send(f"❌ Erro ao obter avisos IPMA: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(IPMA(bot))
