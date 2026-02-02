import os
import json
import random
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from config import GUILD_ID

DATA_FILE = "quem_joga_hoje.json"

def load_players():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_players(players):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

class Bg3Utility(commands.Cog, name="bg3_utilities"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="quem_joga",
        description="Marca quem joga hoje e opcionalmente define o período da sessão"
    )
    @app_commands.describe(
        periodo="Número de horas que temos disponíveis para jogar"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def quem_joga(
        self, context: Context, periodo: int = None
    ) -> None:
        """
        Marca o utilizador que vai jogar hoje.

        :param context: Contexto do comando.
        :param periodo: Opcional. Número de horas disponíveis para jogar.
        """
        players = load_players()
        user = context.author.display_name

        if user not in players:
            players.append(user)
            save_players(players)

        embed = discord.Embed(
            title="🎮 Quem joga hoje?",
            color=0x00FF00
        )

        if players:
            embed.description = "\n".join(f"• {p}" for p in players)
        else:
            embed.description = "Ninguém marcado ainda 😢"

        if periodo:
            embed.set_footer(
                text=f"Período de jogo definido: {periodo} hora(s). Use /reset_jogo para limpar a lista"
            )
        else:
            embed.set_footer(
                text="Use /reset_jogo para limpar a lista"
            )

        await context.send(embed=embed)

    @commands.hybrid_command(
        name="reset_jogo",
        description="Limpa a lista de quem joga hoje"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def reset_jogo(self, context: Context) -> None:
        """
        Limpa a lista de jogadores.

        :param context: Contexto do comando.
        """
        save_players([])
        embed = discord.Embed(
            description="🧹 Lista limpa. Bora marcar outra sessão!",
            color=0x00FF00
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="d20",
        description="Rola um d20 para decisões rápidas"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def d20(self, context: Context) -> None:
        """
        Rola um dado de 20 lados sem gifs.

        :param context: Contexto do comando.
        """
        value = random.randint(1, 20)

        embed = discord.Embed(
            title="🎲 Resultado do d20",
            description=f"**{context.author.display_name} rolou:** **{value}**",
            color=0xFFD700
        )

        if value == 20:
            embed.set_footer(text="🔥 SUCESSO CRÍTICO 🔥")
        elif value == 1:
            embed.set_footer(text="💀 FALHA CRÍTICA 💀")

        await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Bg3Utility(bot))
