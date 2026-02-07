import random
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from selectolax.parser import HTMLParser
from config import GUILD_ID

BASE = "https://epstein-docs.github.io"


# =====================
# Scraping helpers
# =====================

async def fetch(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return await r.text()


def parse(html: str) -> HTMLParser:
    return HTMLParser(html)


async def get_all_documents() -> list[str]:
    html = await fetch(f"{BASE}/all-documents/")
    parser = parse(html)

    doc_ids = []
    for card in parser.css("#results .document-card a"):
        href = card.attributes.get("href")
        if href and href.startswith("/document/"):
            doc_id = href.strip("/").split("/")[-1]
            doc_ids.append(doc_id)

    return list(set(doc_ids))


async def get_document(doc_id: str) -> dict:
    html = await fetch(f"{BASE}/document/{doc_id}/")
    parser = parse(html)

    # ---------------------
    # Title
    # ---------------------
    title = f"Document {doc_id}"
    if h1 := parser.css_first("h1"):
        title = h1.text().strip()

    # ---------------------
    # Analysis summary <strong>
    # ---------------------
    summary = None
    strong = parser.css_first(
        "div.analysis-content div.analysis-summary strong"
    )
    if strong:
        summary = strong.text().strip()

    # ---------------------
    # Preview content
    # ---------------------
    preview = ""
    paragraphs = parser.css("article p")
    for p in paragraphs[:5]:
        preview += p.text().strip() + "\n\n"

    if not preview:
        preview = "_No preview available. Click link to view full document._"

    return {
        "id": doc_id,
        "title": title,
        "summary": summary,
        "preview": preview[:3500],  # safety margin
        "url": f"{BASE}/document/{doc_id}/"
    }


# =====================
# Cog
# =====================

class EpsteinDocsCog(commands.Cog):
    """Random Epstein document picker"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="epstein",
        description="Get a random Epstein document"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def random_doc(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        doc_ids = await get_all_documents()
        if not doc_ids:
            await interaction.followup.send("❌ Could not fetch documents.")
            return

        doc_id = random.choice(doc_ids)
        doc = await get_document(doc_id)

        embed = discord.Embed(
            title=doc["title"],
            description=doc["preview"],
            color=discord.Color.dark_red(),
            url=doc["url"]
        )

        if doc["summary"]:
            embed.add_field(
                name="🧠 Analysis Summary",
                value=f"**{doc['summary']}**",
                inline=False
            )

        embed.set_footer(text=f"Document ID: {doc['id']}")

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="🔗 Open Full Document",
                url=doc["url"],
                style=discord.ButtonStyle.link
            )
        )

        await interaction.followup.send(embed=embed, view=view)


# =====================
# Setup
# =====================

async def setup(bot):
    await bot.add_cog(EpsteinDocsCog(bot))