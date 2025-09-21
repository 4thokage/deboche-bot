import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import aiohttp
import json
from typing import Optional
from config import GUILD_ID

class Santarem(commands.Cog):
    """Comando para mostrar a programação de eventos do Santarém Cultura."""

    BASE_URL = "https://santaremcultura.pt/index.php/programacao/calendario-de-eventos?format=raw"

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="santarem",
        description="Mostra a programação de eventos em Santarém"
    )
    @app_commands.describe(
        start="Data inicial no formato YYYY-MM-DD (opcional)",
        end="Data final no formato YYYY-MM-DD (opcional)"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def santarem(
        self,
        interaction: discord.Interaction,
        start: Optional[str] = None,
        end: Optional[str] = None
    ):
        # Definir datas padrão
        today = datetime.today()
        start_date = start or today.strftime("%Y-%m-%d")
        end_date = end or (today + timedelta(days=7)).strftime("%Y-%m-%d")

        # Montar URL com parâmetros
        url = "https://santaremcultura.pt/index.php/programacao/calendario-de-eventos"
        params = {"format": "raw", "start": start_date, "end": end_date}
        headers = {"User-Agent": "Mozilla/5.0 (DiscordBot/1.0)"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as resp:
                text = await resp.text()
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    await interaction.response.send_message(
                        f"❌ Não foi possível ler os eventos:\n{text[:200]}...", ephemeral=True
                    )
                    return

        if not data:
            await interaction.response.send_message(
                "ℹ️ Não há eventos neste período.",
                ephemeral=True
            )
            return

        # Criar embed
        embed = discord.Embed(
            title=f"Eventos em Santarém ({start_date} → {end_date})",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Santarém Cultura")

        for event in data[:10]:  # Limitar a 10 eventos para não spam
            title = event.get("title", "Sem título")
            start_time = event.get("start", "??")
            url_suffix = event.get("url", "")
            url_full = f"https://santaremcultura.pt{url_suffix}" if url_suffix else None

            start_dt = start_time
            try:
                start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
            except Exception:
                pass

            embed.add_field(
                name=title,
                value=f"🕒 {start_dt}\n🔗 [Link]({url_full})" if url_full else f"🕒 {start_dt}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Santarem(bot))
