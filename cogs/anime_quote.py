import discord
from discord.ext import commands
from discord.ext.commands import Context
import aiohttp
import random


class AnimeQuote(commands.Cog):
    """Cog com frases aleatórias de anime (Krypton-style)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, "session"):
            self.bot.session = aiohttp.ClientSession()

    @commands.hybrid_command(
        name="anime_quote",
        description="Mostra uma citação random de anime"
    )
    async def anime_quote(self, ctx: Context):
        """Mostra uma citação aleatória de anime."""
        await ctx.defer()  # permite responder mais tarde

        try:
            async with self.bot.session.get("https://api.animechan.io/v1/quotes/random") as r:
                if r.status != 200:
                    raise Exception(f"API retornou status {r.message}")
                info = await r.json()

            # Cria embed
            data = info.get("data")
            embed = discord.Embed(
                title="🗯️ Citação de Anime",
                description=info.get("content", "Sem citação disponível."),
                color=0xFF1493
            )
            char = info.get('character')
            embed.set_footer(text=f"{char.get('name')} — {info.get('anime').get('name')}")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Erro a buscar citação: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(AnimeQuote(bot))
