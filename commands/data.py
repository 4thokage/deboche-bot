import os
import re
import aiohttp
import discord
import datetime
from discord import app_commands
from discord.ext import commands
from urllib.parse import quote
from io import BytesIO
from config import GUILD_ID


class Data(commands.Cog):
    """Cog com comandos que obtem dados."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, "session"):
            self.bot.session = aiohttp.ClientSession()

    # --------------------------
    # Screenshot de website
    # --------------------------
    @app_commands.command(
        name="ss",
        description="Tira uma screenshot de um website"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ss(self, interaction: discord.Interaction, website: str):
        """Envia a screenshot de um website"""
        await interaction.response.defer()

        # Remove possíveis <> e espaços
        website = website.strip("<>")

        # Public thum.io URL
        url = f"https://image.thum.io/get/width/1920/crop/675/maxAge/1/noanimate/https://{website}"

        try:
            # Fetch image from thum.io
            headers = {"User-Agent": "DebocheBot/1.0.0"}
            async with self.bot.session.get(url, headers=headers) as r:
                if r.status != 200:
                    body = await r.text()
                    return await interaction.followup.send(
                        f"❌ Erro ao gerar screenshot (HTTP {r.status}):\n{body[:500]}"
                    )
                image_data = await r.read()

            # Send image as attachment
            file = discord.File(BytesIO(image_data), filename="screenshot.png")
            embed = discord.Embed(
                title=website,
                url=f"https://{website}",
                timestamp=datetime.datetime.utcnow(),
                color=discord.Color.random()
            )
            embed.set_image(url="attachment://screenshot.png")
            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao tirar screenshot: {e}")

    @app_commands.command(
        name="hastebin",
        description="Cria um paste no Hastebin com o texto fornecido."
    )
    @app_commands.describe(texto="O texto que queres colar no Hastebin")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.checks.cooldown(1, 15.0)  # 1 utilização a cada 15s por utilizador
    async def hastebin(self, interaction: discord.Interaction, texto: str):
        await interaction.response.defer(thinking=True)

        async with aiohttp.ClientSession() as session:
            async with session.post("https://hastebin.com/documents", data=texto.encode("utf-8")) as resp:
                if resp.status != 200:
                    return await interaction.followup.send(f"❌ Erro ao contactar o Hastebin (HTTP {resp.status})")

                data = await resp.json()
                url = f"https://hastebin.com/{data['key']}"

        embed = discord.Embed(
            title="📌 Paste criado com sucesso!",
            description=url,
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

    # --------------------------
    # Pokédex
    # --------------------------
    @app_commands.command(
        name="pokedex",
        description="Mostra informações sobre um Pokémon"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def pokedex(self, interaction: discord.Interaction, pokemon: str):
        """Mostra informações de um Pokémon da PokeAPI"""
        await interaction.response.defer()

        pokemon = pokemon.lower()
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon}"

        try:
            async with self.bot.session.get(url) as r:
                if r.status == 404:
                    await interaction.followup.send(f"❌ Pokémon '{pokemon}' não encontrado.")
                    return
                data = await r.json()

            # Informações básicas
            nome = data["name"].capitalize()
            altura = data["height"] / 10  # metros
            peso = data["weight"] / 10   # kg
            tipos = ", ".join(t["type"]["name"].capitalize() for t in data["types"])
            habilidades = ", ".join(a["ability"]["name"].replace("-", " ").capitalize() for a in data["abilities"])

            # Estatísticas
            stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}

            # Sprite
            sprite_url = data["sprites"]["front_default"]

            embed = discord.Embed(
                title=f"Pokémon: {nome}",
                description=f"Tipos: {tipos}\nHabilidades: {habilidades}",
                color=0x2F3136
            )
            embed.add_field(name="Altura", value=f"{altura} m")
            embed.add_field(name="Peso", value=f"{peso} kg")
            embed.add_field(
                name="Estatísticas",
                value=(
                    f"HP: {stats.get('hp', 0)}\n"
                    f"Ataque: {stats.get('attack', 0)}\n"
                    f"Defesa: {stats.get('defense', 0)}\n"
                    f"Ataque Especial: {stats.get('special-attack', 0)}\n"
                    f"Defesa Especial: {stats.get('special-defense', 0)}\n"
                    f"Velocidade: {stats.get('speed', 0)}"
                ),
                inline=False
            )
            if sprite_url:
                embed.set_thumbnail(url=sprite_url)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao obter informações do Pokémon: {e}")

    @app_commands.command(
        name="wiki",
        description="Busca um artigo na Wikipedia em inglês"
    )
    @app_commands.describe(termo="O termo que queres pesquisar na Wikipedia")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def wiki(self, interaction: discord.Interaction, termo: str):
        await interaction.response.defer()

        # Formata o termo para URL
        termo_formatado = termo.replace(" ", "_")

        try:
            async with self.bot.session.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{termo_formatado}"
            ) as resp:
                if resp.status == 404:
                    return await interaction.followup.send(f"❌ Nenhum artigo encontrado para `{termo}`")
                data = await resp.json()

                titulo = data.get("title", termo)
                descricao = data.get("extract", "Sem resumo disponível.")
                url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{termo_formatado}")
                imagem = data.get("thumbnail", {}).get("source")

                embed = discord.Embed(
                    title=titulo,
                    description=descricao,
                    url=url,
                    color=discord.Color.blue()
                )
                if imagem:
                    embed.set_thumbnail(url=imagem)
                embed.set_footer(text="Fonte: Wikipedia")

                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"🚨 Algo correu mal: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Data(bot))