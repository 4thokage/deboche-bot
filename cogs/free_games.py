import os
import random

import discord
from discord import app_commands
from discord.ext import commands

GUILD_ID = int(os.getenv("GUILD_ID", 0))


class FreeGamesDB(commands.Cog):
    """Mostra jogos free-to-play"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="free_games",
        description="Mostra um jogo free-to-play aleatório"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def free_games(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            async with self.bot.session.get("https://www.freetogame.com/api/games") as r:
                jogos = await r.json()

            game = random.choice(jogos)
            embed = discord.Embed(
                title=game["title"],
                description=game["short_description"],
                color=0x8A2BE2
            )
            embed.add_field(name="Plataforma", value=game["platform"])
            embed.add_field(name="Genero", value=game["genre"])
            embed.add_field(name="Link", value=game["game_url"], inline=False)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao obter jogos: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(FreeGamesDB(bot))
