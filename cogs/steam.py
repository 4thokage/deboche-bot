import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
from config import GUILD_ID
from paginator import EmbedPaginator


class SteamStocksCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =======================================================================
    #   HELPERS → STEAM
    # =======================================================================

    async def steam_search(self, query: str) -> dict | None:
        """Pesquisa jogos na Steam Store."""
        url = f"https://store.steampowered.com/api/storesearch?term={query}&l=en&cc=EU"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()

    async def steam_details(self, appid: int) -> dict | None:
        """Obtém detalhes completos de um jogo pelo appid."""
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return data.get(str(appid), {}).get("data", None)

    async def steam_discounts(self) -> list[dict]:
        url = "https://store.steampowered.com/api/featuredcategories/?cc=EU"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        discounted_items = []

        for category in data.values():
            if not isinstance(category, dict):
                continue  # ignora valores que não são dicionários
            items = category.get("items", [])
            for item in items:
                if item.get("discount_percent", 0) > 0:
                    discounted_items.append(item)

        return sorted(discounted_items, key=lambda x: x["discount_percent"], reverse=True)


    # =======================================================================
    #   /steamgame
    # =======================================================================

    @app_commands.command(name="steamgame", description="Pesquisar jogos ou ver descontos da Steam.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        mode="pesquisar = procurar jogo | descontos = listar descontos",
        query="Nome do jogo (modo pesquisar)"
    )
    async def steamgame(self, interaction: discord.Interaction, mode: str, query: str | None = None):
        await interaction.response.defer(thinking=True)
        mode = mode.lower()

        # -----------------------------
        #   MODE DESCONTOS
        # -----------------------------
        if mode == "descontos":
            discounts = await self.steam_discounts()

            if not discounts:
                return await interaction.followup.send("❌ Não foi possível obter os descontos.")

            text = ""
            for game in discounts[:30]:
                prev_price = game["original_price"] / 100 if game["original_price"] else 0
                new_price = game["final_price"] / 100 if game["final_price"] else 0

                text += (
                    f"**🔥 {game['name']} — {game['discount_percent']}% OFF**\n"
                    f"💶 Antes: `{prev_price:.2f}€`\n"
                    f"💸 Agora: `{new_price:.2f}€`\n"
                    f"🔗 https://store.steampowered.com/app/{game['id']}\n\n"
                )

            paginator = EmbedPaginator(
                text,
                title="Descontos Steam — Maior → Menor",
                color=0x2ecc71
            )
            return await paginator.start(interaction)

        # -----------------------------
        #   MODE PESQUISAR JOGO
        # -----------------------------
        if mode == "pesquisar":
            if not query:
                return await interaction.followup.send("❌ Tens de fornecer um nome (`query`) para pesquisar.")

            search = await self.steam_search(query)

            if not search or len(search.get("items", [])) == 0:
                return await interaction.followup.send("❌ Jogo não encontrado.")

            game = search["items"][0]
            appid = game["id"]

            details = await self.steam_details(appid)
            if not details:
                return await interaction.followup.send("❌ Não foi possível obter detalhes do jogo.")

            price = details.get("price_overview", {})
            price_text = price.get("final_formatted", "Free to Play")

            embed = discord.Embed(
                title=details["name"],
                url=f"https://store.steampowered.com/app/{appid}",
                description=details.get("short_description", "Sem descrição."),
                color=0x3498db
            )
            embed.set_thumbnail(url=details.get("header_image"))
            embed.add_field(name="💵 Preço", value=price_text)
            embed.add_field(
                name="📅 Data de Lançamento",
                value=details.get("release_date", {}).get("date", "N/A")
            )
            embed.add_field(
                name="🔥 Metacritic",
                value=details.get("metacritic", {}).get("score", "N/A")
            )

            return await interaction.followup.send(embed=embed)

        # -----------------------------
        #   INVALID MODE
        # -----------------------------
        return await interaction.followup.send("❌ Modo inválido. Usa `pesquisar` ou `descontos`.")

async def setup(bot):
    await bot.add_cog(SteamStocksCog(bot))
