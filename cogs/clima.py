import os
import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context

GUILD_ID = int(os.getenv("GUILD_ID", 0))
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

#TODO: add more cities and corresdponding lat lon
COMMON_CITIES = {
    "Lisboa": (38.7169, -9.1395),
    "Porto": (41.1495, -8.6108),
    "Coimbra": (40.2056, -8.4196),
    "Funchal": (32.6669, -16.9241),
    "Santarém": (39.2333, -8.6833),
}

# ---------------- Dropdown ----------------
class CitySelect(discord.ui.Select):
    def __init__(self, cities: list[str]):
        options = [discord.SelectOption(label=c) for c in cities]
        super().__init__(
            placeholder="Escolhe uma cidade...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.value_selected = None

    async def callback(self, interaction: discord.Interaction):
        self.value_selected = self.values[0]
        await interaction.response.defer()
        self.view.stop()


class WeatherView(discord.ui.View):
    def __init__(self, cities: list[str]):
        super().__init__(timeout=30)
        self.select = CitySelect(cities)
        self.add_item(self.select)

# ---------------- Cog ----------------
class Weather(commands.Cog):
    """Clima atual usando OpenWeatherMap (/weather)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, "session"):
            self.bot.session = aiohttp.ClientSession()

    @commands.hybrid_command(
        name="clima",
        description="Mostra o clima atual de uma cidade"
    )
    async def clima(self, ctx: Context, city: str = None):
        if not OPENWEATHER_API_KEY:
            await ctx.send("❌ API Key do OpenWeatherMap não configurada.")
            return

        await ctx.defer()

        if not city:
            view = WeatherView(list(COMMON_CITIES.keys()))
            msg = await ctx.send("🌍 Escolhe a cidade:", view=view)
            await view.wait()

            if not view.select.value_selected:
                await msg.edit(content="❌ Nenhuma cidade selecionada.", view=None)
                return

            city = view.select.value_selected

        coords = COMMON_CITIES.get(city)
        if not coords:
            await ctx.send("❌ Cidade não suportada.")
            return

        lat, lon = coords

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "units": "metric",
            "lang": "pt",
            "appid": OPENWEATHER_API_KEY
        }

        try:
            async with self.bot.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=20)) as r:
                if r.status != 200:
                    raise Exception(f"Erro da API ({r.status})")
                data = await r.json()

            # ---- Dados corretos ----
            main = data["main"]
            weather = data["weather"][0]
            wind = data.get("wind", {})
            clouds = data.get("clouds", {})

            temp = main["temp"]
            feels = main["feels_like"]
            humidity = main["humidity"]
            pressure = main["pressure"]

            wind_ms = wind.get("speed", 0)
            wind_kmh = round(wind_ms * 3.6, 1)
            wind_deg = wind.get("deg", "—")

            cloudiness = clouds.get("all", 0)

            desc = weather["description"].capitalize()
            icon = weather["icon"]

            embed = discord.Embed(
                title=f"🌤️ Clima em {city}",
                description=f"**{desc}**",
                color=0x3498DB
            )

            embed.set_thumbnail(
                url=f"https://openweathermap.org/img/wn/{icon}@2x.png"
            )

            embed.add_field(
                name="🌡️ Temperatura",
                value=f"{temp}°C\nSensação: {feels}°C",
                inline=True
            )
            embed.add_field(
                name="💨 Vento",
                value=f"{wind_kmh} km/h\nDireção: {wind_deg}°",
                inline=True
            )
            embed.add_field(
                name="💧 Humidade",
                value=f"{humidity}%",
                inline=True
            )
            embed.add_field(
                name="🔽 Pressão",
                value=f"{pressure} hPa",
                inline=True
            )
            embed.add_field(
                name="☁️ Nuvens",
                value=f"{cloudiness}%",
                inline=True
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Erro ao obter clima: `{e}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))