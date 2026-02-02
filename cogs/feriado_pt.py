import os

import discord
from discord import app_commands
from discord.ext import commands

GUILD_ID = int(os.getenv("GUILD_ID", 0))


class FeriadoPT(commands.Cog):
    """Feriados nacionais de Portugal"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="feriado_pt",
        description="Mostra o próximo feriado nacional em Portugal"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def feriado_pt(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            async with self.bot.session.get(
                "https://date.nager.at/api/v3/NextPublicHolidays/PT"
            ) as r:
                data = await r.json()

            feriado = data[0]

            embed = discord.Embed(
                title="📅 Próximo Feriado em Portugal",
                description=f"**{feriado['localName']}**",
                color=0x006600
            )
            embed.add_field(name="Data", value=feriado["date"])
            embed.add_field(name="Tipo", value="Feriado Nacional 🇵🇹")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao obter feriado: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(FeriadoPT(bot))
