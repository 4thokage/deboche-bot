import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
from typing import Optional
from config import GUILD_ID


YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": False,
    "extract_flat": False,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "forceipv4": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}


class YTDLSource(discord.PCMVolumeTransformer):
    """Wrapper que usa yt-dlp para criar um stream válido para FFmpeg"""

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")

    @classmethod
    async def from_url(cls, url, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()

        def extract():
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                return ydl.extract_info(url, download=not stream)

        data = await loop.run_in_executor(None, extract)

        # playlists → pega cada entrada
        if "entries" in data:
            data = data["entries"][0]

        if stream:
            # yt-dlp fornece o stream diretamente → evita 403
            return cls(
                discord.FFmpegPCMAudio(
                    data["url"],
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                    options="-vn"
                ),
                data=data
            )
        else:
            filename = ydl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename), data=data)


class Music(commands.Cog):
    """Cog de música robusto com fila"""

    def __init__(self, bot):
        self.bot = bot
        self.guild_queues: dict[int, asyncio.Queue] = {}
        self.guild_playing: dict[int, bool] = {}

    async def play_next(self, guild_id: int, vc: discord.VoiceClient):
        queue = self.guild_queues[guild_id]

        if queue.empty():
            self.guild_playing[guild_id] = False
            await vc.disconnect()
            return

        song = await queue.get()

        # yt-dlp → create stream
        player = await YTDLSource.from_url(song, loop=self.bot.loop, stream=True)

        def after_playing(error):
            if error:
                print(f"Erro: {error}")
            fut = asyncio.run_coroutine_threadsafe(self.play_next(guild_id, vc), self.bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(e)

        vc.play(player, after=after_playing)
        self.guild_playing[guild_id] = True

    @app_commands.command(name="musica", description="Toca música ou playlist")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def musica(self, interaction: discord.Interaction, canal: discord.VoiceChannel, link: str):

        await interaction.response.defer()

        vc: Optional[discord.VoiceClient] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_connected():
            if vc.channel.id != canal.id:
                await vc.move_to(canal)
        else:
            vc = await canal.connect()

        # coloca link direto na queue (yt-dlp faz o resto)
        queue = self.guild_queues.setdefault(interaction.guild.id, asyncio.Queue())
        await queue.put(link)

        await interaction.followup.send(f"🎵 Adicionado à fila: {link}")

        # tocar
        if not self.guild_playing.get(interaction.guild.id, False):
            await self.play_next(interaction.guild.id, vc)

    # CONTROLES
    @app_commands.command(name="pause")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ Pausado.")
        else:
            await interaction.response.send_message("❌ Nada está tocando.", ephemeral=True)

    @app_commands.command(name="resume")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶ Resumido.")
        else:
            await interaction.response.send_message("❌ Não está pausado.", ephemeral=True)

    @app_commands.command(name="stop")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        queue = self.guild_queues.get(interaction.guild.id)

        if vc:
            vc.stop()
            if queue:
                while not queue.empty():
                    await queue.get()
            self.guild_playing[interaction.guild.id] = False
            await vc.disconnect()
            await interaction.response.send_message("⏹ Música parada.")
        else:
            await interaction.response.send_message("❌ Nada está tocando.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Music(bot))
