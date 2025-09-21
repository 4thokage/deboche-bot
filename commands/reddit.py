import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from config import GUILD_ID
import random

class Reddit(commands.Cog):
    """Reddit commands for r/PORTUGALCARALHO"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="reddit",
        description="Mostra um post do r/PORTUGALCARALHO"
    )
    @app_commands.describe(
        sort="Como ordenar os posts (hot, new, top, rising)",
        limit="Número máximo de posts para escolher aleatoriamente (1-50)"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def reddit(
        self,
        interaction: discord.Interaction,
        sort: str = "hot",
        limit: int = 10
    ):
        """Mostra posts de r/PORTUGALCARALHO"""

        await interaction.response.defer()

        sort = sort.lower()
        if sort not in ["hot", "new", "top", "rising"]:
            return await interaction.followup.send("❌ Sort inválido! Use hot, new, top ou rising.")

        limit = max(1, min(limit, 50))  # clamp between 1 and 50

        url = f"https://www.reddit.com/r/PORTUGALCARALHO/{sort}.json?limit={limit}"
        headers = {"User-Agent": "DebocheBot/1.0.0"}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    return await interaction.followup.send(
                        f"❌ Erro ao acessar Reddit (HTTP {resp.status}):\n{body[:500]}"
                    )
                data = await resp.json()

        posts = data.get("data", {}).get("children", [])
        if not posts:
            return await interaction.followup.send("❌ Nenhum post encontrado.")

        # Escolhe aleatoriamente um post
        post = random.choice(posts)["data"]

        title = post.get("title", "Sem título")
        url_post = f"https://reddit.com{post.get('permalink', '')}"
        author = post.get("author", "??")
        ups = post.get("ups", 0)
        downs = post.get("downs", 0)
        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)
        image_url = post.get("url_overridden_by_dest") if post.get("post_hint") == "image" else None

        embed = discord.Embed(
            title=title[:256],
            url=url_post,
            description=f"Autor: u/{author}\nScore: {score} (↑{ups} ↓{downs})\nComentários: {num_comments}",
            color=discord.Color.random()
        )

        if image_url and image_url.endswith(("jpg", "png", "gif", "jpeg")):
            embed.set_image(url=image_url)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Reddit(bot))
