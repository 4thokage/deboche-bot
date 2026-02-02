import os
import aiohttp

import discord
from discord.ext import commands
from discord import app_commands
from config import GUILD_ID


class SimNao(commands.Cog):
    """Respostas sim/não com GIFs"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_gif(self, answer: str) -> str:
        url = f"https://yesno.wtf/api?force={answer}"
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise RuntimeError("API yesno.wtf falhou")
                data = await resp.json()
                return data["image"]

    @commands.hybrid_command(name="sim", description="Resposta SIM (GIF)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def sim(self, ctx: commands.Context):
        try:
            gif_url = await self.fetch_gif("yes")
            await ctx.send(gif_url)
        except Exception:
            await ctx.send("❌ O universo não conseguiu decidir (sim).")

    @commands.hybrid_command(name="nao", description="Resposta NÃO (GIF)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def nao(self, ctx: commands.Context):
        try:
            gif_url = await self.fetch_gif("no")
            await ctx.send(gif_url)
        except Exception:
            await ctx.send("❌ O universo não conseguiu decidir (não).")


async def setup(bot: commands.Bot):
    await bot.add_cog(SimNao(bot))