import discord
from discord.ext import commands
from discord.ext.commands import Context
import aiohttp
from typing import Optional, List

GUILD_ID = 123456789  # replace with your env if needed


class Waifu(commands.Cog):
    """Mostra waifus aleatórias com filtros avançados via waifu.im API (Krypton-style)."""

    BASE_URL = "https://api.waifu.im/search"

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, "session"):
            self.bot.session = aiohttp.ClientSession(headers={"User-Agent": "DebocheBot/1.0.0"})

    @commands.hybrid_command(
        name="waifu",
        description="Mostra uma waifu aleatória filtrada por tags e critérios"
    )
    async def waifu(
        self,
        ctx: Context,
        included_tags: Optional[str] = None,
        excluded_tags: Optional[str] = None,
        is_nsfw: Optional[str] = "false",
        gif: Optional[bool] = False,
        order_by: Optional[str] = None,
        orientation: Optional[str] = None,
        limit: Optional[int] = 1,
        width: Optional[str] = None,
        height: Optional[str] = None,
        byte_size: Optional[str] = None
    ):
        """
        Mostra uma ou mais waifus aleatórias com filtros avançados.

        :param included_tags: Tags separadas por vírgula para incluir
        :param excluded_tags: Tags separadas por vírgula para excluir
        :param is_nsfw: "true", "false" ou "null" para random NSFW
        :param gif: True para permitir apenas gifs
        :param order_by: order criteria
        :param orientation: portrait/landscape/square
        :param limit: Número de imagens (max 30 sem admin)
        :param width: Filtro de largura
        :param height: Filtro de altura
        :param byte_size: Filtro de tamanho do arquivo
        """
        await ctx.defer()

        params = {}
        if included_tags:
            params["included_tags"] = [tag.strip() for tag in included_tags.split(",") if tag.strip()]
        if excluded_tags:
            params["excluded_tags"] = [tag.strip() for tag in excluded_tags.split(",") if tag.strip()]
        if is_nsfw:
            params["is_nsfw"] = is_nsfw
        if gif:
            params["gif"] = True
        if order_by:
            params["order_by"] = order_by
        if orientation:
            params["orientation"] = orientation
        if width:
            params["width"] = width
        if height:
            params["height"] = height
        if byte_size:
            params["byte_size"] = byte_size

        try:
            async with self.bot.session.get(self.BASE_URL, params=params) as r:
                if r.status != 200:
                    text = await r.text()
                    return await ctx.send(f"❌ Erro ao buscar waifu (HTTP {r.status}):\n{text[:500]}")
                data = await r.json()

            images = data.get("images", [])
            if not images:
                return await ctx.send("❌ Nenhuma waifu encontrada com esses filtros.")

            for waifu in images:
                artist = waifu.get("artist") or {}
                tags_list = waifu.get("tags") or []

                embed = discord.Embed(
                    title="Waifu 🖼️",
                    description=(
                        f"**Artist:** {artist.get('name', '??')}\n"
                        f"**Source:** {waifu.get('source', '??')}\n"
                        f"**Tags:** {', '.join(tag.get('name', '??') for tag in tags_list) or '??'}\n"
                        f"**NSFW:** {'Sim' if waifu.get('is_nsfw') else 'Não'}\n"
                        f"**Uploaded:** {waifu.get('uploaded_at', '??')}"
                    ),
                    color=discord.Color.random()
                )

                if waifu.get("url"):
                    embed.set_image(url=waifu["url"])

                embed.set_footer(
                    text=f"Dimensions: {waifu.get('width', '??')}x{waifu.get('height', '??')} | Bytes: {waifu.get('byte_size', '??')}"
                )

                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Erro a buscar waifu: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Waifu(bot))
