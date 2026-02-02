import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from typing import List, Dict, Optional

COCKTAIL_API = "https://www.thecocktaildb.com/api/json/v1/1/search.php"
from config import GUILD_ID


# =========================
# API CLIENT
# =========================

class CocktailClient:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))

    async def close(self):
        if self.session:
            await self.session.close()

    async def search(self, name: str) -> List[Dict]:
        params = {"s": name}

        async with self.session.get(COCKTAIL_API, params=params) as resp:
            if resp.status != 200:
                return []

            data = await resp.json()
            return data.get("drinks") or []


# =========================
# UI COMPONENTS
# =========================

class DrinkSelect(discord.ui.Select):
    def __init__(self, drinks: List[Dict]):
        self.drinks = drinks

        options = [
            discord.SelectOption(
                label=d["strDrink"][:100],
                description=d.get("strCategory", "Cocktail")[:100],
                value=str(i),
            )
            for i, d in enumerate(drinks[:25])  # Discord hard limit
        ]

        super().__init__(
            placeholder="🍸 Escolhe um cocktail",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        drink = self.drinks[int(self.values[0])]
        embed = build_drink_embed(drink)
        await interaction.response.edit_message(embed=embed, view=None)


class DrinkSelectView(discord.ui.View):
    def __init__(self, drinks: List[Dict]):
        super().__init__(timeout=60)
        self.add_item(DrinkSelect(drinks))


# =========================
# EMBED BUILDER
# =========================

def build_drink_embed(drink: Dict) -> discord.Embed:
    embed = discord.Embed(
        title=drink["strDrink"],
        color=0xe67e22,
    )

    if thumb := drink.get("strDrinkThumb"):
        embed.set_thumbnail(url=thumb)

    embed.add_field(
        name="🍷 Categoria",
        value=drink.get("strCategory", "—"),
        inline=True,
    )
    embed.add_field(
        name="🥃 Tipo",
        value=drink.get("strAlcoholic", "—"),
        inline=True,
    )
    embed.add_field(
        name="🍸 Copo",
        value=drink.get("strGlass", "—"),
        inline=True,
    )

    # Ingredients
    ingredients = []
    for i in range(1, 16):
        ing = drink.get(f"strIngredient{i}")
        if not ing:
            continue
        measure = drink.get(f"strMeasure{i}") or ""
        ingredients.append(f"• {measure.strip()} {ing}")

    embed.add_field(
        name="🧾 Ingredientes",
        value="\n".join(ingredients) or "—",
        inline=False,
    )

    embed.add_field(
        name="📖 Instruções",
        value=drink.get("strInstructions", "—")[:1024],
        inline=False,
    )

    embed.set_footer(text="Fonte: TheCocktailDB 🍹")
    return embed


# =========================
# COG
# =========================

class Cocktails(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = CocktailClient()

    async def cog_load(self):
        await self.client.start()

    async def cog_unload(self):
        await self.client.close()

    @app_commands.command(
        name="cocktail",
        description="Pesquisar cocktails pelo nome 🍸",
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def cocktail(self, interaction: discord.Interaction, nome: str):
        await interaction.response.defer(thinking=True)

        drinks = await self.client.search(nome)

        if not drinks:
            return await interaction.followup.send(
                "❌ Não encontrei nenhum cocktail com esse nome."
            )

        # Single result → straight to details
        if len(drinks) == 1:
            embed = build_drink_embed(drinks[0])
            return await interaction.followup.send(embed=embed)

        # Multiple → dropdown
        view = DrinkSelectView(drinks)
        await interaction.followup.send(
            content="Encontrei vários cocktails 👇",
            view=view,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Cocktails(bot))