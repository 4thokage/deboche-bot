import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
from typing import Optional
from config import GUILD_ID

class Music(commands.Cog):
    """Cog de música robusto com YouTube e playlists"""

    def __init__(self, bot):
        self.bot = bot
        self.guild_queues: dict[int, asyncio.Queue] = {}  # fila de músicas por guild
        self.guild_playing: dict[int, bool] = {}          # estado de reprodução

    async def get_yt_info(self, url: str) -> list[dict]:
        """Retorna lista de dicionários com 'url' e 'title'"""
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "extract_flat": True,  # extrai playlists sem baixar
        }

        loop = asyncio.get_event_loop()

        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                entries = []
                if "entries" in info:  # playlist
                    for e in info["entries"]:
                        # Re-extract para pegar URL do audio
                        full_info = ydl.extract_info(e["url"], download=False)
                        entries.append({"url": full_info["url"], "title": full_info["title"]})
                else:
                    entries.append({"url": info["url"], "title": info["title"]})
                return entries

        return await loop.run_in_executor(None, _extract)

    async def play_next(self, guild_id: int, vc: discord.VoiceClient):
        """Toca a próxima música da fila"""
        queue = self.guild_queues[guild_id]
        if queue.empty():
            self.guild_playing[guild_id] = False
            await vc.disconnect()
            return

        song = await queue.get()
        source = discord.FFmpegPCMAudio(
            song["url"],
            options="-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )

        def after_playing(error):
            if error:
                print(f"Erro ao tocar música: {error}")
            # Chama recursivamente para próxima música
            fut = asyncio.run_coroutine_threadsafe(self.play_next(guild_id, vc), self.bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(e)

        vc.play(source, after=after_playing)
        self.guild_playing[guild_id] = True

    @app_commands.command(
        name="musica",
        description="Toca música ou playlist num canal de voz"
    )
    @app_commands.describe(
        canal="Canal de voz onde tocar",
        link="Link do YouTube (vídeo ou playlist)"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def musica(self, interaction: discord.Interaction, canal: discord.VoiceChannel, link: str):
        await interaction.response.defer(thinking=True)

        vc: Optional[discord.VoiceClient] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_connected():
            if vc.channel.id != canal.id:
                await vc.move_to(canal)
        else:
            vc = await canal.connect()

        # Pega informações da música/playlist
        try:
            entries = await self.get_yt_info(link)
        except Exception as e:
            return await interaction.followup.send(f"❌ Falha ao obter info: {e}")

        # Inicializa fila se não existir
        queue = self.guild_queues.setdefault(interaction.guild.id, asyncio.Queue())
        for entry in entries:
            await queue.put(entry)

        first_song = entries[0]
        await interaction.followup.send(
            f"🎶 Adicionado(s) à fila:\n" +
            "\n".join(f"- {e['title']}" for e in entries)
        )

        # Toca se não estiver tocando
        if not self.guild_playing.get(interaction.guild.id, False):
            await self.play_next(interaction.guild.id, vc)

    # --- Comandos de controle ---
    @app_commands.command(name="pause", description="Pausa a música atual")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def pause(self, interaction: discord.Interaction):
        vc: Optional[discord.VoiceClient] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ Música pausada")
        else:
            await interaction.response.send_message("❌ Nada está tocando", ephemeral=True)

    @app_commands.command(name="resume", description="Resume a música pausada")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def resume(self, interaction: discord.Interaction):
        vc: Optional[discord.VoiceClient] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶ Música retomada")
        else:
            await interaction.response.send_message("❌ Nada está pausado", ephemeral=True)

    @app_commands.command(name="stop", description="Para a música e limpa a fila")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def stop(self, interaction: discord.Interaction):
        vc: Optional[discord.VoiceClient] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        queue: asyncio.Queue = self.guild_queues.get(interaction.guild.id)
        if vc:
            vc.stop()
            if queue:
                while not queue.empty():
                    await queue.get()
            self.guild_playing[interaction.guild.id] = False
            await vc.disconnect()
            await interaction.response.send_message("⏹ Música parada e fila limpa")
        else:
            await interaction.response.send_message("❌ Nada está tocando", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Music(bot))
