import os
import discord
import asyncio
import datetime
import aiohttp
from discord import app_commands
from discord.ext import commands
import random

GUILD_ID = int(os.getenv("GUILD_ID", 0)) if "GUILD_ID" in os.environ else None

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="conselho",
        description="Gera um conselho em inglês ou português"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))  # for instant testing
    # @app_commands.describe(lang="Idioma: en (inglês) ou pt (português)")
    async def conselho(self, interaction: discord.Interaction, lang: str = "pt"):
        """
        Fetches a random advice from https://api.adviceslip.com/advice
        and optionally translates it to Portuguese using MyMemory API.
        """
        await interaction.response.defer(thinking=True)
        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache"
        }

        try:
            # --- fetch advice ---
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.adviceslip.com/advice",
                    headers=headers,
                ) as resp:
                    data = await resp.json(content_type=None)
                    advice = data["slip"]["advice"]

                # --- translate advice ---
                translate_url = (
                    "https://api.mymemory.translated.net/get"
                    f"?q={advice}&langpair=en|pt"
                )
                async with session.get(translate_url) as tr:
                    tr_json = await tr.json()
                    pt_advice = tr_json["responseData"]["translatedText"]

            await interaction.followup.send(f"💡 {advice}\n🇵🇹 {pt_advice}")

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao buscar ou traduzir: {e}")


    @app_commands.command(
        name="bolacha",
        description="Quem consegue apanhar a bolacha primeiro?"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def bolacha(self, interaction: discord.Interaction):
        """Desafio: apanha a bolacha!"""
        
        # Send initial message
        await interaction.response.send_message(embed=discord.Embed(title="🍪 Atenção! A bolacha está a chegar..."))
        m = await interaction.original_response()

        # Countdown
        for i in range(3, 0, -1):
            await m.edit(embed=discord.Embed(title=f"🍪 A bolacha chega em **{i}**..."))
            await asyncio.sleep(1)

        # Start challenge
        start = datetime.datetime.utcnow()

        class CookieButton(discord.ui.View):
            def __init__(self, bot, start_time):
                super().__init__(timeout=10)
                self.bot = bot
                self.start = start_time
                self.winner = None

            @discord.ui.button(label="🍪 Apanhar!", style=discord.ButtonStyle.primary)
            async def catch(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.winner is None:
                    self.winner = interaction.user
                    tempo = round((datetime.datetime.utcnow() - self.start).total_seconds() - self.bot.latency, 3)
                    # Disable all buttons
                    for child in self.children:
                        child.disabled = True
                    await interaction.response.edit_message(
                        embed=discord.Embed(title=f"🎉 **{self.winner.display_name}** apanhou a bolacha em **{tempo} segundos!**"),
                        view=self
                    )
                    self.stop()

        # Attach the button to the message, passing bot and start time
        await m.edit(
            embed=discord.Embed(title="🍪 Clique no botão para apanhar a bolacha!"),
            view=CookieButton(self.bot, start)
        )

    @app_commands.command(
        name="penis",
        description="Vê o tamanho do pénis de alguém (aleatório)"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def penis(self, interaction: discord.Interaction, membro: discord.Member = None):
        """Comando para ver o tamanho do pénis de alguém de forma aleatória"""
        membro = membro or interaction.user
        tamanho = random.randint(0, 30)

        # Comentários baseados no tamanho
        comentarios = {
            0: "hehe, pénis pequenino 😅",
            6: "ok",
            10: "pénis normal",
            13: "pénis grande",
            19: "pénis enorme 😳",
            26: "pénis monstruoso 😱",
        }
        comentario = closest_smaller(comentarios, tamanho)

        # Construir a representação visual do pp
        representacao = f'8{"=" * tamanho}D'

        embed = discord.Embed(
            title=f"Tamanho do pénis de {membro.display_name}",
            description=representacao,
            color=0x2F3136
        )
        embed.set_footer(text=comentario)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="bola_de_cristal",
        description="Consulta a bola de cristal para obter uma resposta misteriosa!"
    )
    @app_commands.describe(pergunta="A tua pergunta para a bola mágica")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def eight_ball(self, interaction: discord.Interaction, pergunta: str):
        respostas = [
            "É certo.",
            "Sem dúvida!",
            "Definitivamente sim.",
            "Podes contar com isso.",
            "Tudo indica que sim.",
            "A meu ver, sim.",
            "Muito provavelmente.",
            "As perspetivas são boas.",
            "Os sinais apontam para sim.",
            "Resposta incerta, tenta outra vez.",
            "Pergunta de novo mais tarde.",
            "Melhor não te dizer agora.",
            "Não consigo prever agora.",
            "Concentra-te e pergunta de novo.",
            "Não contes com isso.",
            "A minha resposta é não.",
            "As minhas fontes dizem que não.",
            "As perspetivas não são boas.",
            "Muito duvidoso…"
        ]

        resposta = random.choice(respostas)

        embed = discord.Embed(
            title="🎱 Bola de Cristal",
            description=f"**Pergunta:** {pergunta}\n\n**Resposta:** {resposta}",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Não leves demasiado a sério 😉")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="bola_de_berlim",
        description="Recebe uma deliciosa Bola de Berlim em ASCII 😋"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def bola_de_berlim(self, interaction: discord.Interaction):
        ascii_berlim = r"""
         ,--./,-.
        / #      \
       |          |
        \        /   
         `._,._,'
          (o_o)
        _.-' '-._
       /         \
      |           |
       \_________/
        """

        embed = discord.Embed(
            title="🍩 Bola de Berlim!",
            description=f"```\n{ascii_berlim}\n```",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Não dá para comer… mas quase! 😄")

        await interaction.response.send_message(embed=embed)
    
    #TODO: mover isto    
    @app_commands.command(
        name="sync",
        description="Sincroniza todos os comandos de aplicação com o servidor."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def sync_tree(self, interaction: discord.Interaction):
        """Força a sincronização do app command tree"""
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            synced = await self.bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            await interaction.followup.send(
                f"✅ Sincronizados {len(synced)} comandos para este servidor."
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao sincronizar comandos:\n`{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))


def closest_smaller(d: dict, key: int):
    """Retorna o valor associado à maior chave menor ou igual à key."""
    keys = sorted(d.keys())
    for k in reversed(keys):
        if key >= k:
            return d[k]
    return ""