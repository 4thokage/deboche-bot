import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from typing import Dict, List, Final
from selectolax.parser import HTMLParser
from contextlib import suppress
from config import GUILD_ID

BASE_URL: Final[str] = "https://www3.gogoanimes.fi/"


# =====================
# Scraper helpers
# =====================

async def get_request(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


def html_parser(html: str) -> HTMLParser:
    return HTMLParser(html)


async def search_anime(query: str) -> List[Dict[str, str]]:
    html = await get_request(f"{BASE_URL}/search.html?keyword={query}")
    parser = html_parser(html)

    results = []
    for element in parser.css("div.last_episodes ul.items li"):
        name = element.css_first("p a").attributes["title"]
        img = element.css_first("div a img").attributes["src"]
        anime_id = element.css_first("div a").attributes["href"].split("/")[-1]

        results.append({
            "name": name,
            "img": img,
            "id": anime_id
        })

    return results


async def get_streaming_links(anime_id: str, episode: int) -> Dict[str, str]:
    html = await get_request(f"{BASE_URL}/{anime_id}-episode-{episode}")
    parser = html_parser(html)

    servers = parser.css(".anime_muti_link > ul > li")[1:]
    data = {}

    for server in servers:
        server_name = server.attributes.get("class", "unknown")
        link = server.css_first("a").attributes.get("data-video")
        data[server_name] = link

    return data


# =====================
# Discord UI
# =====================

class AnimeResultView(discord.ui.View):
    def __init__(self, anime_id: str):
        super().__init__(timeout=120)
        self.anime_id = anime_id

    @discord.ui.button(label="▶️ Get Episode 1 Links", style=discord.ButtonStyle.primary)
    async def get_links(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.defer(thinking=True)

        links = await get_streaming_links(self.anime_id, 1)

        if not links:
            await interaction.followup.send("❌ No streaming links found.")
            return

        msg = "**🎬 Streaming Links (Episode 1):**\n"
        for server, url in links.items():
            msg += f"• **{server}** → {url}\n"

        await interaction.followup.send(msg)


# =====================
# Cog
# =====================

class AnimeCog(commands.Cog):
    """Search anime and get streaming links"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="anime", description="Search for an anime")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(query="Anime name")
    async def anime_search(
        self,
        interaction: discord.Interaction,
        query: str
    ):
        await interaction.response.defer(thinking=True)

        results = await search_anime(query)

        if not results:
            await interaction.followup.send("❌ No results found.")
            return

        for anime in results[:5]:  # limit spam
            print(anime)
            embed = discord.Embed(
                title=anime["name"],
                description=f"ID: `{anime['id']}`",
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=BASE_URL + anime["img"])

            view = AnimeResultView(anime["id"])

            await interaction.followup.send(
                embed=embed,
                view=view
            )


# =====================
# Setup
# =====================

async def setup(bot: commands.Bot):
    await bot.add_cog(AnimeCog(bot))