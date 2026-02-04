import aiohttp

import discord
from discord.ext import commands
from discord import app_commands
from config import GUILD_ID

XKCD_LATEST_API = "https://xkcd.com/info.0.json"


class Internet(commands.Cog):
    """Comic diário do XKCD"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_latest_comic(self) -> dict:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get(XKCD_LATEST_API) as resp:
                if resp.status != 200:
                    raise RuntimeError("XKCD API falhou")
                return await resp.json()

    @commands.hybrid_command(
        name="xkcd",
        description="Mostra o comic diário do XKCD"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def xkcd(self, ctx: commands.Context):
        try:
            comic = await self.fetch_latest_comic()

            embed = discord.Embed(
                title=f"XKCD #{comic['num']} — {comic['title']}",
                description=comic.get("alt", ""),
                color=0xFFFFFF,
                url=f"https://xkcd.com/{comic['num']}/"
            )

            embed.set_image(url=comic["img"])

            embed.set_footer(
                text=f"{comic['day']}/{comic['month']}/{comic['year']}"
            )

            await ctx.send(embed=embed)

        except Exception:
            await ctx.send("❌ Não consegui buscar o XKCD de hoje.")

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


async def setup(bot: commands.Bot):
    await bot.add_cog(Internet(bot))