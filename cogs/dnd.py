import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from config import GUILD_ID

BASE_API = "https://www.dnd5eapi.co/api/2014/features"

class DnDFeatures(commands.Cog):
    """Mostra features do D&D 5e com dropdown"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_features_list(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_API) as resp:
                if resp.status != 200:
                    raise RuntimeError("Falha ao buscar features")
                data = await resp.json()
                return data.get("results", [])

    async def fetch_feature(self, feature_index: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_API}/{feature_index}") as resp:
                if resp.status != 200:
                    raise RuntimeError("Falha ao buscar feature")
                return await resp.json()

    @commands.hybrid_command(
        name="dnd",
        description="Escolhe uma feature de D&D 5e"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def feature(self, ctx: commands.Context):
        await ctx.defer()

        try:
            features = await self.fetch_features_list()
            if not features:
                await ctx.send("❌ Lista de features vazia.")
                return

            # Preparar opções para o dropdown
            options = [
                discord.SelectOption(label=f["name"], value=f["index"])
                for f in features[:25]  # Discord tem limite de 25 opções por dropdown
            ]

            select = discord.ui.Select(
                placeholder="Escolhe uma feature...",
                options=options,
                min_values=1,
                max_values=1
            )

            async def callback(interaction: discord.Interaction):
                index = select.values[0]
                feature = await self.fetch_feature(index)

                desc = "\n".join(feature.get("desc", ["Sem descrição"]))
                class_name = feature.get("class", {}).get("name", "N/A")
                level = feature.get("level", "N/A")

                embed = discord.Embed(
                    title=feature.get("name", "Feature"),
                    description=desc,
                    color=0x1F8B4C
                )
                embed.add_field(name="Classe", value=class_name, inline=True)
                embed.add_field(name="Level", value=str(level), inline=True)
                embed.set_footer(text="Fonte: dnd5eapi.co")

                await interaction.response.send_message(embed=embed, ephemeral=True)

            select.callback = callback
            view = discord.ui.View()
            view.add_item(select)

            await ctx.send("Escolhe uma feature abaixo:", view=view)

        except Exception as e:
            await ctx.send(f"❌ Falha ao buscar features: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(DnDFeatures(bot))