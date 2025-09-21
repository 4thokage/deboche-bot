import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from config import GUILD_ID


class Anime(commands.Cog):
    """Waifu commands using the official API with tag parameters"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="waifu",
        description="Mostra uma waifu aleatória com detalhes filtrada por tags"
    )
    @app_commands.describe(
        tags="Tags separadas por vírgula, ex: raiden-shogun,maid"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def waifu(
        self,
        interaction: discord.Interaction,
        tags: str = ""
    ):
        await interaction.response.defer()

        # Split the comma-separated tags and strip spaces
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        url = "https://api.waifu.im/search"
        params = {"included_tags": tags_list}
        headers = {"User-Agent": "DebocheBot/1.0.0"}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    return await interaction.followup.send(
                        f"❌ Erro ao buscar waifu (HTTP {resp.status}):\n{body[:500]}"
                    )
                data = await resp.json()

        if not data.get("images"):
            return await interaction.followup.send("❌ Nenhuma waifu encontrada com essas tags.")

        waifu = data["images"][0]
        
        artist = waifu.get("artist") or {}
        tags = waifu.get("tags") or []

        embed = discord.Embed(
            title="Waifu",
            description=f"**Artist:** {artist.get('name', '??')}\n"
                        f"**Source:** {waifu.get('source', '??')}\n"
                        f"**Tags:** {', '.join(tag.get('name', '??') for tag in tags) or '??'}\n"
                        f"**NSFW:** {'Sim' if waifu.get('is_nsfw') else 'Não'}\n"
                        f"**Uploaded:** {waifu.get('uploaded_at', '??')}",
            color=discord.Color.random()
        )
        if waifu.get("url"):
            embed.set_image(url=waifu["url"])

        embed.set_footer(text=f"Dimensions: {waifu.get('width', '??')}x{waifu.get('height', '??')} | Bytes: {waifu.get('byte_size', '??')}")

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Anime(bot))
