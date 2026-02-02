import os

import discord
from discord import app_commands
from discord.ext import commands

GUILD_ID = int(os.getenv("GUILD_ID", 0))


class CountryInfo(commands.Cog):
    """Mostra informação de um país"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="pais",
        description="Mostra informação sobre um país"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def pais(self, interaction: discord.Interaction, nome: str):
        await interaction.response.defer()

        try:
            async with self.bot.session.get(f"https://restcountries.com/v3.1/name/{nome}") as r:
                data = await r.json()

            country = data[0]
            name = country["name"]["common"]
            capital = ", ".join(country.get("capital", ["?"]))
            population = country.get("population", "?")
            flag = country.get("flags", {}).get("png", "")

            embed = discord.Embed(
                title=f"🌍 {name}",
                color=0x4682B4
            )
            embed.set_thumbnail(url=flag)
            embed.add_field(name="Capital", value=capital)
            embed.add_field(name="População", value=f"{population:,}")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Não consegui obter informação: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(CountryInfo(bot))
