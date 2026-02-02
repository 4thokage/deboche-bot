import aiohttp

import discord
from discord.ext import commands
from discord import app_commands
from config import GUILD_ID

XKCD_LATEST_API = "https://xkcd.com/info.0.json"


class XKCD(commands.Cog):
    """Comic diário do XKCD"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_latest_comic(self) -> dict:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get(XKCD_LATEST_API) as resp:
                if resp.status != 200:
                    raise RuntimeError("XKCD API falhou")
                return await resp.json()

    @commands.hybrid_command(
        name="xkcd",
        description="Mostra o comic diário do XKCD"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def xkcd(self, ctx: commands.Context):
        try:
            comic = await self.fetch_latest_comic()

            embed = discord.Embed(
                title=f"XKCD #{comic['num']} — {comic['title']}",
                description=comic.get("alt", ""),
                color=0xFFFFFF,
                url=f"https://xkcd.com/{comic['num']}/"
            )

            embed.set_image(url=comic["img"])

            embed.set_footer(
                text=f"{comic['day']}/{comic['month']}/{comic['year']}"
            )

            await ctx.send(embed=embed)

        except Exception:
            await ctx.send("❌ Não consegui buscar o XKCD de hoje.")


async def setup(bot: commands.Bot):
    await bot.add_cog(XKCD(bot))