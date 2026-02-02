import os
import discord
from discord.ext import commands
from discord import app_commands
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.async_api import async_playwright
from discord.ext import commands

# Mapear categorias para os seus URLs
CATEGORIES = {
    "opiniao": "https://omirante.pt/opiniao",
    "cultura-e-lazer": "https://omirante.pt/cultura-e-lazer",
    "desporto": "https://omirante.pt/desporto",
    "economia": "https://omirante.pt/economia",
    "politica": "https://omirante.pt/politica",
    "sociedade": "https://omirante.pt/sociedade",
    "ultimas": "https://omirante.pt",
}


class News(commands.Cog):
    """Comando para buscar notícias do O Mirante."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="mirante",
        description="Busca as últimas notícias do O Mirante."
    )
    @app_commands.describe(
        n_resultados="Número de notícias a mostrar (1 a 10, default 5).",
        categoria="Categoria: opiniao, cultura-e-lazer, desporto, economia, politica, sociedade, ultimas"
    )
    @app_commands.guilds(discord.Object(id=int(os.getenv("GUILD_ID"))))
    async def mirante(
        self,
        interaction: discord.Interaction,
        n_resultados: int = 5,
        categoria: str = "opiniao",
    ):
        """Slash command /mirante para buscar notícias."""
        await interaction.response.defer(thinking=True)

        cat = categoria.lower()
        url = CATEGORIES.get(cat, CATEGORIES["ultimas"])
        n_resultados = max(1, min(n_resultados, 10))

        try:
            # Iniciar Playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle")  # espera o JS carregar
                html = await page.content()
                await browser.close()

            # Parse HTML com BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Encontrar blocos de notícias
            blocks = soup.select("div.newList, div.new")  # classe usada pelo site
            if not blocks:
                return await interaction.followup.send("⚠️ Nenhuma notícia encontrada.")

            noticias = []
            for block in blocks[:n_resultados]:
                title_tag = block.select_one(".title h1")
                lead_tag = block.select_one(".lead h2, .body")
                link_tag = block.select_one("a[href]")
                date_tag = block.select_one("input[datetime]")

                titulo = title_tag.get_text(strip=True) if title_tag else "Sem título"
                desc = lead_tag.get_text(strip=True) if lead_tag else ""
                link = link_tag["href"] if link_tag else "#"
                if not link.startswith("http"):
                    link = "https://omirante.pt" + link

                data_pub = date_tag.get("datetime") if date_tag else ""
                try:
                    data_fmt = (
                        datetime.fromisoformat(data_pub)
                        .strftime("%d/%m/%Y %H:%M")
                        if data_pub
                        else ""
                    )
                except ValueError:
                    data_fmt = data_pub

                noticias.append(
                    f"**[{titulo}]({link})**\n"
                    f"{desc}\n"
                    f"🗓️ {data_fmt}\n"
                )

            await interaction.followup.send("\n\n".join(noticias))

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao processar notícias: `{e}`")


    @commands.hybrid_command(name="mirante")
    async def mirante_text(self, ctx: commands.Context, n_resultados: int = 5, categoria: str = "opiniao"):
        """Permite usar o comando via texto, ex: !mirante 2 cultura-e-lazer"""
        # Criamos um "fake interaction" para reaproveitar o código do slash
        class DummyInteraction:
            def __init__(self, ctx):
                self.ctx = ctx

            async def response_defer(self, thinking=True):
                await self.ctx.send("⏳ A buscar notícias...")

            async def followup_send(self, content):
                await self.ctx.send(content)

            @property
            def response(self):
                return self

            async def defer(self, thinking=True):
                await self.ctx.send("⏳ A buscar notícias...")

            async def send(self, content):
                await self.ctx.send(content)

            async def followup(self, send=None, **kwargs):
                if send:
                    await self.ctx.send(send)
                elif "content" in kwargs:
                    await self.ctx.send(kwargs["content"])

        fake_interaction = DummyInteraction(ctx)
        # Reaproveitar o método slash
        await self.mirante.__func__(self, fake_interaction, n_resultados, categoria)

async def setup(bot: commands.Bot):
    await bot.add_cog(News(bot))
