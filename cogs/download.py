import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
import asyncio
import aiohttp
from config import GUILD_ID

class DownloaderCog(commands.Cog):
    """Download videos or audio (mp3) from URLs"""

    def __init__(self, bot):
        self.bot = bot

    async def run_yt_dlp(self, url: str, audio: bool = False) -> str | None:
        """Download video/audio with yt-dlp. Returns filepath or None if fail."""
        outtmpl = "downloads/%(title).50s.%(ext)s"
        ydl_opts = {
            "outtmpl": outtmpl,
            "quiet": True,
            "noplaylist": True,
        }

        if audio:
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            ydl_opts.update({"format": "mp4"})

        os.makedirs("downloads", exist_ok=True)

        loop = asyncio.get_event_loop()
        try:
            filepath = None
            def _dl():
                nonlocal filepath
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filepath = ydl.prepare_filename(info)
                    if audio:
                        filepath = os.path.splitext(filepath)[0] + ".mp3"
            await loop.run_in_executor(None, _dl)
            return filepath
        except Exception as e:
            print("yt-dlp error:", e)
            return None

    async def upload_to_transfersh(self, filepath: str) -> str | None:
        """Upload file to transfer.sh and return the download URL"""
        filename = os.path.basename(filepath)
        url = "https://temp.sh/upload"
        try:
            async with aiohttp.ClientSession() as session:
                with open(filepath, "rb") as f:
                    data = {"file": f}
                    async with session.post(url, data=data) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            return text.strip()
                        else:
                            print("temp.sh error:", resp.status)
                            return None
        except Exception as e:
            print("Upload error:", e)
            return None

    @app_commands.command(name="download", description="Baixar vídeo ou áudio de um URL")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(url="Link do vídeo/música", audio="Baixar apenas áudio (mp3)?")
    async def download(self, interaction: discord.Interaction, url: str, audio: bool = False):
        await interaction.response.defer(thinking=True)

        filepath = await self.run_yt_dlp(url, audio)
        if not filepath or not os.path.exists(filepath):
            await interaction.followup.send("❌ Falha ao baixar.")
            return

        try:
            if os.path.getsize(filepath) < 8 * 1024 * 1024:
                await interaction.followup.send(file=discord.File(filepath))
            else:
                link = await self.upload_to_transfersh(filepath)
                if link:
                    await interaction.followup.send(f"⚠️ Arquivo muito grande, mas está disponível aqui:\n{link}")
                else:
                    await interaction.followup.send("❌ Arquivo baixado mas não consegui enviar/upload.")
        finally:
            os.remove(filepath)

async def setup(bot):
    await bot.add_cog(DownloaderCog(bot))
