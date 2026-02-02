import os
import random

import discord
from discord import app_commands
from discord.ext import commands

GUILD_ID = int(os.getenv("GUILD_ID", 0))


class Benfica(commands.Cog):
    """Frases míticas do SL Benfica"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.frases = [
            "🗣️ «Ser Benfiquista é ter na alma a chama imensa.» – Eusébio",
            "🗣️ «O Benfica não é um clube, é uma nação.»",
            "🗣️ «Enquanto houver 11 benfiquistas em campo, há esperança.»",
            "🗣️ «O Benfica é maior que qualquer jogador, treinador ou presidente.»",
            "🗣️ «No Benfica não se joga, representa-se.»",
            "🗣️ «Perder faz parte. Desistir nunca.»",
            "🗣️ «O Benfica não precisa de ajuda, precisa de respeito.»",
            "🗣️ «Ganhámos hoje? Então está tudo bem.» – Adepto comum",
            "🗣️ «Eles podem não gostar, mas têm de aceitar.»",
            "🗣️ «Aqui não se fala de pressão. Fala-se de responsabilidade.»",
            "🗣️ «O Benfica joga sempre para ganhar.»",
            "🗣️ «Quando o Benfica ganha, ganha Portugal.»",
            "🗣️ «A Luz não intimida. A Luz impõe respeito.»",
            "🗣️ «O silêncio dos outros fala alto quando o Benfica vence.»",
            "🗣️ «O Benfica não se explica, sente-se.»"
        ]

    # --------------------------
    # Frase mítica do Benfica
    # --------------------------
    @app_commands.command(
        name="benfica_frase",
        description="Mostra uma frase mítica do SL Benfica"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def benfica_frase(self, interaction: discord.Interaction):
        await interaction.response.defer()

        frase = random.choice(self.frases)

        embed = discord.Embed(
            title="🦅 Frase Mítica do SL Benfica",
            description=frase,
            color=0xE10600
        )
        embed.set_footer(text="E pluribus unum 🔴⚪")

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Benfica(bot))
