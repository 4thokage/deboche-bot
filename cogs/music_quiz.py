import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
from typing import Optional
from config import GUILD_ID
import random

class MusicQuiz(commands.Cog):
    """Cog de quiz de música usando YouTube"""

    def __init__(self, bot):
        self.bot = bot
        self.guild_queues: dict[int, asyncio.Queue] = {}  # fila de músicas por guild
        self.guild_playing: dict[int, bool] = {}          # estado de reprodução
        self.scores: dict[int, dict[int, int]] = {}       # guild_id -> user_id -> score

    async def get_yt_info(self, urls: list[str]) -> list[dict]:
        """Retorna lista de dicionários com 'url' e 'title'"""
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "extract_flat": True,
        }

        loop = asyncio.get_event_loop()

        def _extract():
            entries = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for url in urls:
                    info = ydl.extract_info(url, download=False)
                    if "entries" in info:  # playlist
                        for e in info["entries"]:
                            full_info = ydl.extract_info(e["url"], download=False)
                            entries.append({"url": full_info["url"], "title": full_info["title"]})
                    else:
                        entries.append({"url": info["url"], "title": info["title"]})
            return entries

        return await loop.run_in_executor(None, _extract)

    async def play_quiz(self, guild_id: int, vc: discord.VoiceClient):
        """Toca a próxima música do quiz"""
        queue = self.guild_queues[guild_id]
        if queue.empty():
            self.guild_playing[guild_id] = False
            await vc.disconnect()
            return

        song = await queue.get()
        source = discord.FFmpegPCMAudio(
            song["url"],
            options="-vn -t 10 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -fflags +genpts"  # toca só 10s
        )

        def after_playing(error):
            if error:
                print(f"Erro ao tocar música: {error}")
            fut = asyncio.run_coroutine_threadsafe(self.play_quiz(guild_id, vc), self.bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(e)

        vc.play(source, after=after_playing)
        self.guild_playing[guild_id] = True

    @app_commands.command(
        name="music_quiz",
        description="Começa um quiz de música no canal de voz"
    )
    @app_commands.describe(
        canal="Canal de voz onde tocar",
        urls="Links do YouTube separados por espaço"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def music_quiz(self, interaction: discord.Interaction, canal: discord.VoiceChannel, urls: str):
        await interaction.response.defer(thinking=True)
        url_list = urls.split()

        vc: Optional[discord.VoiceClient] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_connected():
            if vc.channel.id != canal.id:
                await vc.move_to(canal)
        else:
            vc = await canal.connect()

        # Pega informações das músicas
        try:
            entries = await self.get_yt_info(url_list)
        except Exception as e:
            return await interaction.followup.send(f"❌ Falha ao obter info: {e}")

        # Inicializa fila se não existir
        queue = self.guild_queues.setdefault(interaction.guild.id, asyncio.Queue())
        for entry in entries:
            await queue.put(entry)

        # Inicializa score
        self.scores.setdefault(interaction.guild.id, {})

        # Começa o quiz
        await interaction.followup.send(
            f"🎵 Quiz iniciado! Tenta adivinhar a música tocando no canal {canal.mention}"
        )

        await self.play_quiz(interaction.guild.id, vc)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Detecta respostas no chat e dá pontos"""
        if message.author.bot:
            return
        guild_id = message.guild.id
        queue = self.guild_queues.get(guild_id)
        if not queue or queue.empty():
            return

        # Pega a música atual
        current_song = queue._queue[0] if not queue.empty() else None
        if not current_song:
            return

        # Checa se acertou
        if current_song["title"].lower() in message.content.lower():
            user_scores = self.scores.setdefault(guild_id, {})
            user_scores[message.author.id] = user_scores.get(message.author.id, 0) + 1
            await message.channel.send(f"✅ {message.author.mention} acertou! Pontos: {user_scores[message.author.id]}")

            # Pula música atual
            vc: Optional[discord.VoiceClient] = discord.utils.get(self.bot.voice_clients, guild=message.guild)
            if vc:
                vc.stop()

async def setup(bot):
    await bot.add_cog(MusicQuiz(bot))
