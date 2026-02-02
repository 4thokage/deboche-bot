import os
import random
import aiohttp

import discord
from discord import app_commands
from discord.ext import commands
from config import GUILD_ID

GAMERPOWER_API = (
    "https://www.gamerpower.com/api/giveaways"
    "?platform=steam&type=loot&sort-by=popularity"
)


class SteamLoot(commands.Cog):
    """Giveaways Steam (loot/DLC) via GamerPower"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_giveaways(self) -> list[dict]:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get(GAMERPOWER_API) as resp:
                if resp.status != 200:
                    raise RuntimeError("API GamerPower falhou")
                return await resp.json()

    @app_commands.command(
        name="steam_loot",
        description="Mostra um giveaway de loot/DLC grátis na Steam"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def steam_loot(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        try:
            giveaways = await self.fetch_giveaways()
            if not giveaways:
                raise RuntimeError("Lista vazia")

            giveaway = random.choice(giveaways)

            embed = discord.Embed(
                title=giveaway["title"],
                description=giveaway["description"],
                color=0x1B2838,  # Steam vibes
                url=giveaway.get("gamerpower_url"),
            )

            embed.set_thumbnail(url=giveaway.get("thumbnail"))

            embed.add_field(
                name="🧩 Tipo",
                value=giveaway.get("type", "N/A"),
                inline=True
            )
            embed.add_field(
                name="🖥️ Plataforma",
                value=giveaway.get("platforms", "Steam"),
                inline=True
            )
            embed.add_field(
                name="👥 Utilizadores",
                value=str(giveaway.get("users", "N/A")),
                inline=True
            )

            end_date = giveaway.get("end_date", "N/A")
            embed.add_field(
                name="⏳ Termina",
                value=end_date if end_date != "N/A" else "Sem data limite",
                inline=False
            )

            embed.add_field(
                name="📜 Como reclamar",
                value=giveaway.get("instructions", "Ver link abaixo"),
                inline=False
            )

            embed.set_footer(
                text="Fonte: gamerpower.com"
            )

            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="🎁 Reclamar Giveaway",
                    url=giveaway.get("open_giveaway_url"),
                    style=discord.ButtonStyle.link
                )
            )

            await interaction.followup.send(embed=embed, view=view)

        except Exception:
            await interaction.followup.send(
                "❌ Não consegui buscar giveaways agora. A Steam também está triste.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(SteamLoot(bot))