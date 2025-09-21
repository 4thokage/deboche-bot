import os
import random
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

GUILD_ID = int(os.getenv("GUILD_ID", 0))


class Espaco(commands.Cog):
    """Comandos relacionados com o espaço"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_key = getattr(bot, "api_keys", {}).get("nasa", "DEMO_KEY")

    # --------------------------
    # Foto do Dia da NASA
    # --------------------------
    @app_commands.command(
        name="foto_do_dia",
        description="Mostra a foto do dia da NASA (Astronomy Picture of the Day)"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def foto_do_dia(self, interaction: discord.Interaction, data: str = None):
        await interaction.response.defer()
        params = {"api_key": self.api_key}
        if data:
            params["date"] = data
        try:
            async with self.bot.session.get("https://api.nasa.gov/planetary/apod", params=params) as r:
                resp = await r.json()

            copyright_text = f"\n©️ {resp['copyright']}" if resp.get("copyright") else ""
            embed = discord.Embed(
                title=resp.get("title", "Sem título"),
                description=resp.get("explanation", "Sem descrição"),
                color=0x1E90FF
            )
            embed.set_image(url=resp.get("hdurl") or resp.get("url"))
            embed.set_footer(text=f"Tirada a {resp.get('date', 'desconhecida')}{copyright_text}")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Não foi possível obter a foto do dia: {e}")

    # --------------------------
    # Objetos próximos da Terra
    # --------------------------
    @app_commands.command(
        name="objetos_proximos",
        description="Lista objetos próximos da Terra (asteroides)"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def objetos_proximos(self, interaction: discord.Interaction, data: str = None):
        await interaction.response.defer()
        params = {"api_key": self.api_key}
        if data:
            params["start_date"] = data
            params["end_date"] = data
        try:
            async with self.bot.session.get("https://api.nasa.gov/neo/rest/v1/feed", params=params) as r:
                resp = await r.json()

            neos = list(resp["near_earth_objects"].items())[0][1][:5]  # mostrar apenas os primeiros 5
            if not neos:
                await interaction.followup.send("Nenhum objeto próximo da Terra encontrado.")
                return

            for obj in neos:
                embed = discord.Embed(
                    title=obj["name"],
                    url=obj["nasa_jpl_url"],
                    color=0xFF4500 if obj["is_potentially_hazardous_asteroid"] else 0x32CD32
                )
                diam_min = round(obj["estimated_diameter"]["kilometers"]["estimated_diameter_min"], 2)
                diam_max = round(obj["estimated_diameter"]["kilometers"]["estimated_diameter_max"], 2)
                embed.add_field(name="Diâmetro estimado (km)", value=f"{diam_min} - {diam_max}", inline=False)

                if obj["close_approach_data"]:
                    cad = obj["close_approach_data"][0]
                    epoch = cad["epoch_date_close_approach"] // 1000
                    vel_km = round(float(cad["relative_velocity"]["kilometers_per_hour"]), 2)
                    dist_km = round(float(cad["miss_distance"]["kilometers"]), 2)
                    embed.add_field(
                        name="Passagem próxima",
                        value=f"Data: <t:{epoch}:f>\nVelocidade: {vel_km} km/h\nDistância: {dist_km} km",
                        inline=False
                    )
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Não foi possível obter objetos próximos da Terra: {e}")

    # --------------------------
    # Foto aleatória do rover em Marte
    # --------------------------
    @app_commands.command(
        name="foto_marte",
        description="Mostra uma foto aleatória de um rover em Marte"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def foto_marte(self, interaction: discord.Interaction, rover: str = None):
        await interaction.response.defer()
        rover = rover.lower() if rover else random.choice(["curiosity", "opportunity", "spirit"])
        sol_max = {"curiosity": 3234, "spirit": 2208, "opportunity": 5107}[rover]
        params = {"api_key": self.api_key, "sol": random.randint(0, sol_max)}

        try:
            async with self.bot.session.get(f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos", params=params) as r:
                resp = await r.json()

            photos = resp.get("photos", [])[:3]  # limitar a 3 fotos
            if not photos:
                await interaction.followup.send("Nenhuma foto encontrada.")
                return

            for img in photos:
                earth_date = datetime.fromisoformat(img["earth_date"])
                embed = discord.Embed(
                    title=f"Foto tirada pelo rover {rover.capitalize()}",
                    color=0x1E90FF
                )
                embed.set_image(url=img["img_src"])
                embed.add_field(
                    name="Data (Terra)",
                    value=f"{discord.utils.format_dt(earth_date, 'f')} ({discord.utils.format_dt(earth_date, 'R')})"
                )
                embed.add_field(name="Câmera", value=img["camera"]["full_name"])
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Não foi possível obter fotos do Marte: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Espaco(bot))
