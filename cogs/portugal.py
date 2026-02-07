import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import random
import json
from datetime import datetime, timedelta
from typing import Optional
import xml.etree.ElementTree as ET

from config import GUILD_ID

# --------------------------
# Todos os concelhos de Portugal
# --------------------------
CONCELHOS_PT = {
    "Aveiro": ["Aveiro", "Águeda", "Albergaria-a-Velha", "Anadia", "Arouca", "Espinho", "Oliveira de Azeméis",
               "Ovar", "Santa Maria da Feira", "São João da Madeira", "Sever do Vouga", "Vagos", "Vale de Cambra"],
    # ... resto omitido para brevidade, manter todos os concelhos originais
}
EVIL_INSULT_API = "https://evilinsult.com/generate_insult.php?lang=pt&type=json"


class Portugal(commands.Cog):
    """Comandos sobre Portugal"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, "session"):
            self.bot.session = aiohttp.ClientSession()

    # --------------------------
    # Concelhos
    # --------------------------
    @app_commands.command(
        name="concelho",
        description="Lista todos os concelhos de Portugal"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def concelho(self, interaction: discord.Interaction):
        """Retorna todos os concelhos de Portugal organizados por distrito"""
        await interaction.response.defer()
        embed = discord.Embed(
            title="Concelhos de Portugal",
            description="Organizados por distrito",
            color=0x2F3136
        )
        for distrito, concelhos in CONCELHOS_PT.items():
            embed.add_field(name=distrito, value=", ".join(concelhos), inline=False)
        await interaction.followup.send(embed=embed)

    # --------------------------
    # Fogos
    # --------------------------
    @app_commands.command(
        name="fogos",
        description="Lista todos os fogos ativos em Portugal"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def fogos(self, interaction: discord.Interaction):
        """Mostra fogos ativos em Portugal"""
        await interaction.response.defer()
        url = "https://api.fogos.pt/new/fires"
        headers = {"User-Agent": "DebocheBot/1.0.0"}

        try:
            async with self.bot.session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    return await interaction.followup.send(f"❌ Erro ao buscar fogos (HTTP {resp.status}):\n{body[:500]}")
                data = await resp.json()

            fires = data.get("data", [])
            if not fires:
                return await interaction.followup.send("✅ Nenhum fogo ativo no momento.")

            embed = discord.Embed(
                title="Fogos Ativos em Portugal",
                description=f"{len(fires)} fogo(s) ativo(s) atualmente",
                color=0xE74C3C
            )

            for fire in fires[:10]:
                location = fire.get("location", "Desconhecida")
                district = fire.get("district", "??")
                concelho = fire.get("concelho", "??")
                status = fire.get("status", "??")
                date = fire.get("date", "??")
                hour = fire.get("hour", "??")
                important = "⚠️" if fire.get("important") else ""
                embed.add_field(
                    name=f"{location} ({district} - {concelho})",
                    value=f"Status: {status} {important}\nData: {date} {hour}",
                    inline=False
                )

            embed.set_footer(text="Fonte: api.fogos.pt")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao buscar fogos: {e}")

    # --------------------------
    # Feriados
    # --------------------------
    @app_commands.command(
        name="feriados",
        description="Mostra todos os feriados de Portugal para o ano atual"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def feriados(self, interaction: discord.Interaction):
        await interaction.response.defer()
        year = datetime.now().year
        url = f"https://services.sapo.pt/Holiday/GetAllHolidays?year={year}"

        try:
            async with self.bot.session.get(url) as resp:
                if resp.status != 200:
                    return await interaction.followup.send(f"❌ Erro ao buscar feriados (HTTP {resp.status})")
                text = await resp.text()

            root = ET.fromstring(text)
            holidays = [
                f"{holiday.findtext('{*}Date', '???')}: {holiday.findtext('{*}Name', '???')}"
                for holiday in root.findall(".//{*}Holiday")
            ]

            if not holidays:
                return await interaction.followup.send("✅ Nenhum feriado encontrado.")

            embed = discord.Embed(
                title=f"Feriados em Portugal ({year})",
                description="\n".join(holidays[:10]),
                color=0x3498DB
            )
            embed.set_footer(text="Fonte: services.sapo.pt")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao processar feriados: {e}")

    # --------------------------
    # Futebol
    # --------------------------
    @app_commands.command(
        name="futebol",
        description="Mostra os próximos jogos da Primeira Liga (TheSportsDB)."
    )
    @app_commands.describe(limite="Número máximo de jogos a mostrar (1-10).")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def futebol(self, interaction: discord.Interaction, limite: int = 5):
        await interaction.response.defer(thinking=True)
        limite = max(1, min(limite, 10))
        url = "https://www.thesportsdb.com/api/v1/json/123/eventsseason.php?id=4344&s=2025-2026"

        try:
            async with self.bot.session.get(url) as resp:
                if resp.status != 200:
                    return await interaction.followup.send(f"❌ Falha ao aceder à API (HTTP {resp.status}).")
                payload = await resp.json()

            eventos = payload.get("events", [])
            if not eventos:
                return await interaction.followup.send("⚠️ Nenhum jogo encontrado.")

            jogos = []
            for ev in eventos:
                ts = ev.get("strTimestamp")
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
                jogos.append((dt, ev))

            jogos.sort(key=lambda x: (x[0] is None, x[0]))

            for dt, ev in jogos[:limite]:
                home = ev.get("strHomeTeam", "?")
                away = ev.get("strAwayTeam", "?")
                venue = ev.get("strVenue", "—")
                thumb = ev.get("strThumb")
                status = ev.get("strStatus", "")
                data_txt = dt.strftime('%d/%m/%Y %H:%M UTC') if dt else "Data não disponível"

                embed = discord.Embed(
                    title=f"{home} vs {away}",
                    description=f"🏟️ {venue}\n📅 {data_txt}\n{status}",
                    color=discord.Color.green()
                )
                if thumb:
                    embed.set_thumbnail(url=thumb)
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao processar jogos: {e}")

    # --------------------------
    # Eventos Santarém
    # --------------------------
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
        await interaction.response.defer()
        today = datetime.today()
        start_date = start or today.strftime("%Y-%m-%d")
        end_date = end or (today + timedelta(days=7)).strftime("%Y-%m-%d")

        url = "https://santaremcultura.pt/index.php/programacao/calendario-de-eventos"
        params = {"format": "raw", "start": start_date, "end": end_date}
        headers = {"User-Agent": "Mozilla/5.0 (DiscordBot/1.0)"}

        try:
            async with self.bot.session.get(url, params=params, headers=headers) as resp:
                text = await resp.text()
                data = json.loads(text)
        except Exception:
            return await interaction.followup.send("❌ Não foi possível ler os eventos de Santarém.")

        if not data:
            return await interaction.followup.send("ℹ️ Não há eventos neste período.")

        embed = discord.Embed(
            title=f"Eventos em Santarém ({start_date} → {end_date})",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Santarém Cultura")

        for event in data[:10]:
            title = event.get("title", "Sem título")
            start_time = event.get("start", "??")
            url_suffix = event.get("url", "")
            url_full = f"https://santaremcultura.pt{url_suffix}" if url_suffix else None

            try:
                start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
            except Exception:
                start_dt = start_time

            embed.add_field(
                name=title,
                value=f"🕒 {start_dt}\n🔗 [Link]({url_full})" if url_full else f"🕒 {start_dt}",
                inline=False
            )

        await interaction.followup.send(embed=embed)
        
    @app_commands.command(
        name="feriado_pt",
        description="Mostra o próximo feriado nacional em Portugal"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def feriado_pt(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            async with self.bot.session.get(
                "https://date.nager.at/api/v3/NextPublicHolidays/PT"
            ) as r:
                data = await r.json()

            feriado = data[0]

            embed = discord.Embed(
                title="📅 Próximo Feriado em Portugal",
                description=f"**{feriado['localName']}**",
                color=0x006600
            )
            embed.add_field(name="Data", value=feriado["date"])
            embed.add_field(name="Tipo", value="Feriado Nacional 🇵🇹")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao obter feriado: {e}")


    async def fetch_insulto(self) -> str:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(EVIL_INSULT_API) as resp:
                    if resp.status != 200:
                        raise RuntimeError("API não respondeu 200")

                    data = await resp.json()
                    return data.get("insult", "Hoje não há insultos, só desilusão.")
        except Exception:
            return "A API falhou… tal como tu nesse jogo."

    @app_commands.command(
        name="insulto_tuga",
        description="Recebe um insulto à tuga (sem chorar)"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def insulto_tuga(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        insulto = await self.fetch_insulto()

        embed = discord.Embed(
            title="🇵🇹 Insulto Tuga",
            description=insulto,
            color=0xE10600
        )

        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Portugal(bot))