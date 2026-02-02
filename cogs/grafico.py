import io
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from config import GUILD_ID

class Grafico(commands.Cog):
    """Gera gráficos custom via QuickChart"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_chart(self, chart_config: str) -> bytes:
        """Recebe o chart config (JSON-like) e retorna PNG"""
        url = f"https://quickchart.io/chart?c={chart_config}"
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise RuntimeError("QuickChart API falhou")
                return await resp.read()

    @commands.hybrid_command(
        name="grafico",
        description="Gera um gráfico custom: /grafico tipo=bar labels=2019,2020 valores=10,20"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def grafico(
        self,
        ctx: commands.Context,
        tipo: str = "bar",
        labels: str = "2019,2020,2021,2022,2023",
        valores: str = "120,60,50,180,120",
        titulo: str = "Gráfico Custom"
    ):
        """
        Args:
            tipo: bar, line, pie, radar...
            labels: lista separada por vírgulas
            valores: lista de valores separada por vírgulas
            titulo: título do gráfico
        """
        await ctx.defer()
        try:
            label_list = [l.strip() for l in labels.split(",")]
            value_list = [float(v.strip()) for v in valores.split(",")]

            # Construindo o JSON do gráfico (QuickChart aceita assim)
            chart_json = (
                f"{{type:'{tipo}',data:{{labels:{label_list},datasets:[{{label:'{titulo}',data:{value_list}}}]}}}}"
            )

            image_bytes = await self.fetch_chart(chart_json)

            file = discord.File(
                fp=io.BytesIO(image_bytes),
                filename="grafico.png"
            )

            embed = discord.Embed(
                title=f"📊 {titulo}",
                color=0x5865F2
            )
            embed.set_image(url="attachment://grafico.png")

            await ctx.send(embed=embed, file=file)

        except Exception as e:
            await ctx.send(f"❌ Falhou ao gerar gráfico: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Grafico(bot))