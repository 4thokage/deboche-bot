import os
import random

import discord
from discord import app_commands
from discord.ext import commands

GUILD_ID = int(os.getenv("GUILD_ID", 0))


class ElogioDuvidoso(commands.Cog):
    """Elogios que parecem insultos"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.elogios = [
            "👏 És surpreendentemente competente… para alguém como tu.",
            "💪 Jogas melhor do que parecia à primeira vista.",
            "🧠 Não és tão burro como pareces. Parabéns.",
            "😎 Tens talento. Pena é não o usares sempre.",
            "🎯 Hoje jogaste bem. Aproveita, não é todos os dias.",
            "🔥 És consistente… consistentemente mediano.",
            "👍 Fizeste o mínimo. E isso já foi bom.",
            "🫡 Esperava pior, sinceramente."
        ]

    @app_commands.command(
        name="elogio_duvidoso",
        description="Recebe um elogio que parece um insulto"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def elogio_duvidoso(self, interaction: discord.Interaction):
        await interaction.response.defer()

        frase = random.choice(self.elogios)

        embed = discord.Embed(
            title="🤨 Elogio Duvidoso",
            description=frase,
            color=0xFFD700
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ElogioDuvidoso(bot))
