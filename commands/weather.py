import os
import re
import aiohttp
import discord
import datetime
from discord import app_commands
from discord.ext import commands
from urllib.parse import quote
from io import BytesIO

GUILD_ID = int(os.getenv("GUILD_ID", 0))


class Weather(commands.Cog):
    """Cog com comandos sobre o clima."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, "session"):
            self.bot.session = aiohttp.ClientSession()

    # --------------------------
    # Clima
    # --------------------------
    @app_commands.command(
        name="clima",
        description="Mostra a informação do clima de uma localização"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def clima(self, interaction: discord.Interaction, local: str = "Santarém"):
        """Mostra o clima de uma cidade"""
        await interaction.response.defer()
        
        url = f"https://wttr.in/{local}?format=j1&lang=pt"
        try:
          timeout = aiohttp.ClientTimeout(total=30)
          async with self.bot.session.get(url, timeout=timeout) as r:
              data = await r.json()

          # Dados atuais
          current = data["current_condition"][0]
          temperatura = current["temp_C"]
          sensacao = current["FeelsLikeC"]
          vento_kmh = current["windspeedKmph"]
          vento_dir = current["winddir16Point"]
          tempo_desc = current["lang_pt"][0]["value"]
          humidade = current["humidity"]
          pressao = current["pressure"]
          visibilidade = current["visibility"]
          nuvens = current["cloudcover"]
          uv_index = current["uvIndex"]
          
          # Previsão para os próximos dias
          forecast = data["weather"]
          forecast_text = ""
          for day in forecast:
              date = day["date"]
              maxtemp = day["maxtempC"]
              mintemp = day["mintempC"]
              avgtemp = day["avgtempC"]
              sunhour = day.get("sunHour", "N/A")
              forecast_desc = day["hourly"][0]["lang_pt"][0]["value"]
              forecast_text += f"**{date}**: {forecast_desc}, {mintemp}°C - {maxtemp}°C, média: {avgtemp}°C, sol: {sunhour}\n"

          # Criando embed completo
          embed = discord.Embed(
              title=f"Clima em {local.capitalize()}",
              description=f"**{tempo_desc}**",
              color=0x2F3136
          )
          embed.add_field(name="Temperatura", value=f"{temperatura}°C (Sensação: {sensacao}°C)", inline=True)
          embed.add_field(name="Vento", value=f"{vento_kmh} km/h ({vento_dir})", inline=True)
          embed.add_field(name="Humidade", value=f"{humidade}%", inline=True)
          embed.add_field(name="Pressão", value=f"{pressao} hPa", inline=True)
          embed.add_field(name="Visibilidade", value=f"{visibilidade} km", inline=True)
          embed.add_field(name="Nuvens", value=f"{nuvens}%", inline=True)
          embed.add_field(name="Índice UV", value=f"{uv_index}", inline=True)
          embed.add_field(name="Previsão próximos dias", value=forecast_text, inline=False)

          await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao obter informações do clima: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))