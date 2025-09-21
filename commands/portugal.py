import os
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from config import GUILD_ID
import random
from datetime import datetime
import xml.etree.ElementTree as ET

# Todos os concelhos de Portugal por distrito
CONCELHOS_PT = {
    "Aveiro": ["Aveiro", "Águeda", "Albergaria-a-Velha", "Anadia", "Arouca", "Espinho", "Oliveira de Azeméis",
               "Ovar", "Santa Maria da Feira", "São João da Madeira", "Sever do Vouga", "Vagos", "Vale de Cambra"],
    "Beja": ["Beja", "Aljustrel", "Almodôvar", "Alvito", "Barrancos", "Castro Verde", "Cuba", "Ferreira do Alentejo",
             "Mértola", "Moura", "Odemira", "Ourique", "Serpa", "Vidigueira"],
    "Braga": ["Braga", "Barcelos", "Cabeceiras de Basto", "Celorico de Basto", "Esposende", "Fafe", "Guimarães",
              "Póvoa de Lanhoso", "Terras de Bouro", "Vieira do Minho", "Vila Nova de Famalicão", "Vila Verde", "Vizela"],
    "Bragança": ["Bragança", "Carrazeda de Ansiães", "Vimioso", "Miranda do Douro", "Mogadouro", "Vila Flor", "Vila Pouca de Aguiar",
                 "Alfândega da Fé", "Macedo de Cavaleiros", "Freixo de Espada à Cinta", "Mogadouro", "Torre de Moncorvo", "Mirandela"],
    "Castelo Branco": ["Castelo Branco", "Belmonte", "Covilhã", "Fundão", "Idanha-a-Nova", "Oleiros", "Proença-a-Nova",
                       "Sertã", "Vila de Rei", "Vila Velha de Ródão"],
    "Coimbra": ["Coimbra", "Arganil", "Cantanhede", "Condeixa-a-Nova", "Figueira da Foz", "Góis", "Lousã",
                "Mira", "Miranda do Corvo", "Montemor-o-Velho", "Oliveira do Hospital", "Pampilhosa da Serra", "Penacova",
                "Penela", "Soure", "Vila Nova de Poiares"],
    "Évora": ["Évora", "Alandroal", "Arraiolos", "Borba", "Estremoz", "Montemor-o-Novo", "Moura", "Vendas Novas",
              "Viana do Alentejo", "Vila Viçosa", "Reguengos de Monsaraz", "Redondo", "Portel", "Sousel"],
    "Faro": ["Faro", "Albufeira", "Alcoutim", "Aljezur", "Castro Marim", "Lagoa", "Lagos", "Loulé", "Monchique",
             "Olhão", "Portimão", "São Brás de Alportel", "Silves", "Tavira", "Vila do Bispo", "Vila Real de Santo António"],
    "Guarda": ["Guarda", "Aguiar da Beira", "Almeida", "Celorico da Beira", "Figueira de Castelo Rodrigo", "Fornos de Algodres",
               "Gouveia", "Manteigas", "Meda", "Pinhel", "Sabugal", "Seia", "Trancoso", "Vila Nova de Foz Côa"],
    "Leiria": ["Leiria", "Alcobaça", "Alvaiázere", "Ansião", "Batalha", "Bombarral", "Caldas da Rainha", "Castanheira de Pera",
               "Figueiró dos Vinhos", "Leiria", "Marinha Grande", "Nazaré", "Óbidos", "Pedrógão Grande", "Peniche", "Pombal", "Porto de Mós"],
    "Lisboa": ["Lisboa", "Alcochete", "Alenquer", "Amadora", "Arruda dos Vinhos", "Azambuja", "Cadaval", "Cascais",
               "Lisboa", "Loures", "Lourinhã", "Mafra", "Odivelas", "Oeiras", "Sintra", "Sobral de Monte Agraço", "Torres Vedras", "Vila Franca de Xira"],
    "Portalegre": ["Portalegre", "Alter do Chão", "Arronches", "Avis", "Campo Maior", "Crato", "Elvas", "Fronteira",
                   "Marvão", "Monforte", "Nisa", "Ponte de Sor", "Sousel"],
    "Porto": ["Porto", "Amarante", "Baixa da Banheira", "Câmara de Lobos", "Felgueiras", "Gondomar", "Lousada", "Maia",
              "Matosinhos", "Paços de Ferreira", "Paredes", "Penafiel", "Porto", "Póvoa de Varzim", "Santo Tirso", "Trofa", "Valongo", "Vila do Conde", "Vila Nova de Gaia"],
    "Santarém": ["Santarém", "Abrantes", "Alcanena", "Almeirim", "Alpiarça", "Benavente", "Cartaxo", "Chamusca",
                 "Constância", "Coruche", "Entroncamento", "Ferreira do Zêzere", "Golegã", "Rio Maior", "Salvaterra de Magos", "Santarém", "Sardoal", "Tomar", "Torres Novas", "Vila Nova da Barquinha"],
    "Setúbal": ["Setúbal", "Alcácer do Sal", "Alcochete", "Grândola", "Palmela", "Santiago do Cacém", "Seixal",
                "Sesimbra", "Setúbal", "Sines", "Barreiro", "Moita", "Montijo", "Palmela"],
    "Viana do Castelo": ["Viana do Castelo", "Arcos de Valdevez", "Caminha", "Melgaço", "Monção", "Paredes de Coura",
                         "Ponte de Lima", "Valença", "Viana do Castelo", "Vila Nova de Cerveira"],
    "Vila Real": ["Vila Real", "Alijó", "Boticas", "Chaves", "Mesão Frio", "Mondim de Basto", "Montalegre", "Murça",
                  "Peso da Régua", "Ribeira de Pena", "Santa Marta de Penaguião", "Sabrosa", "Valpaços", "Vila Real", "Vila Pouca de Aguiar"],
    "Viseu": ["Viseu", "Armamar", "Carregal do Sal", "Castro Daire", "Cinfães", "Lamego", "Mangualde", "Moimenta da Beira",
              "Mortágua", "Nelas", "Oliveira de Frades", "Penedono", "Peso da Régua", "São João da Pesqueira", "Sátão",
              "São Pedro do Sul", "Sernancelhe", "Tabuaço", "Tarouca", "Tondela", "Vouzela"]
}

class Portugal(commands.Cog):
    """Comandos sobre Portugal"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="concelho",
        description="Lista todos os concelhos de Portugal"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def concelho(self, interaction: discord.Interaction):
        """Retorna todos os concelhos de Portugal"""
        await interaction.response.defer()

        embed = discord.Embed(
            title="Concelhos de Portugal",
            description="Organizados por distrito",
            color=0x2F3136
        )

        for distrito, concelhos in CONCELHOS_PT.items():
            embed.add_field(name=distrito, value=", ".join(concelhos), inline=False)

        await interaction.followup.send(embed=embed)
        
    @app_commands.command(
        name="fogos",
        description="Lista todos os fogos ativos em Portugal"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def fogos(self, interaction: discord.Interaction):
        """Mostra todos os fogos ativos em Portugal"""
        await interaction.response.defer()

        url = "https://api.fogos.pt/new/fires"
        headers = {"User-Agent": "DebocheBot/1.0.0"}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    return await interaction.followup.send(
                        f"❌ Erro ao buscar fogos (HTTP {resp.status}):\n{body[:500]}"
                    )
                data = await resp.json()

        fires = data.get("data", [])
        if not fires:
            return await interaction.followup.send("✅ Nenhum fogo ativo no momento.")

        embed = discord.Embed(
            title="Fogos Ativos em Portugal",
            description=f"{len(fires)} fogo(s) ativo(s) atualmente",
            color=0xE74C3C
        )

        # Mostra até 10 fogos no embed
        for fire in fires[:10]:
            location = fire.get("location") or "Desconhecida"
            district = fire.get("district") or "??"
            concelho = fire.get("concelho") or "??"
            status = fire.get("status") or "??"
            date = fire.get("date") or "??"
            hour = fire.get("hour") or "??"
            important = "⚠️" if fire.get("important") else ""
            embed.add_field(
                name=f"{location} ({district} - {concelho})",
                value=f"Status: {status} {important}\nData: {date} {hour}",
                inline=False
            )

        embed.set_footer(text="Fonte: api.fogos.pt")
        await interaction.followup.send(embed=embed)
        
    @app_commands.command(
        name="feriados",
        description="Mostra todos os feriados de Portugal para o ano atual"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def feriados(self, interaction: discord.Interaction):
      await interaction.response.defer()
      year = datetime.now().year
      url = f"https://services.sapo.pt/Holiday/GetAllHolidays?year={year}"

      async with aiohttp.ClientSession() as session:
          async with session.get(url) as resp:
              if resp.status != 200:
                  return await interaction.followup.send(
                      f"❌ Erro ao buscar feriados (HTTP {resp.status})"
                  )
              text = await resp.text()
              print(text)

      # Parse XML
      root = ET.fromstring(text)
      holidays = []
      for holiday in root.findall(".//{*}Holiday"):
          name = holiday.findtext("{*}Name") or "???"
          date = holiday.findtext("{*}Date") or "???"
          holidays.append(f"{date}: {name}")

      if not holidays:
          return await interaction.followup.send("✅ Nenhum feriado encontrado.")

      embed = discord.Embed(
          title=f"Feriados em Portugal ({year})",
          description="\n".join(holidays[:10]),  # mostra até 10
          color=0x3498DB
      )
      embed.set_footer(text="Fonte: services.sapo.pt")
      await interaction.followup.send(embed=embed)


    @app_commands.command(
        name="futebol",
        description="Mostra os próximos jogos da Primeira Liga (TheSportsDB)."
    )
    @app_commands.describe(
        limite="Número máximo de jogos a mostrar (1-10)."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def futebol(self, interaction: discord.Interaction, limite: int = 5):
        await interaction.response.defer(thinking=True)
        limite = max(1, min(limite, 10))

        url = (
            f"https://www.thesportsdb.com/api/v1/json/123/eventsseason.php"
            f"?id=4344&s=2025-2026"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send(
                            f"❌ Falha ao aceder à API (HTTP {resp.status})."
                        )
                    payload = await resp.json()

            eventos = payload.get("events")
            if not eventos:
                return await interaction.followup.send("⚠️ Nenhum jogo encontrado.")

            jogos = []
            for ev in eventos:
                ts = ev.get("strTimestamp")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except Exception:
                        dt = None
                else:
                    dt = None
                jogos.append((dt, ev))

            # Ordena pela data (eventos sem data vão para o fim)
            jogos.sort(key=lambda x: (x[0] is None, x[0]))

            embeds = []
            for dt, ev in jogos[:limite]:
                home = ev.get("strHomeTeam", "?")
                away = ev.get("strAwayTeam", "?")
                venue = ev.get("strVenue", "—")
                thumb = ev.get("strThumb")
                status = ev.get("strStatus", "")

                if dt:
                    data_txt = dt.strftime('%d/%m/%Y %H:%M UTC')
                else:
                    data_txt = "Data não disponível"

                embed = discord.Embed(
                    title=f"{home} vs {away}",
                    description=f"🏟️ {venue}\n📅 {data_txt}\n{status}",
                    color=discord.Color.green()
                )
                if thumb:
                    embed.set_thumbnail(url=thumb)
                embeds.append(embed)

            for em in embeds:
                await interaction.followup.send(embed=em)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao processar jogos: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(Portugal(bot))
