import os
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

HISCORES_URL = "https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={}"

SKILLS = [
    "TOTAL","Attack", "Defence", "Strength", "Hitpoints", "Ranged", "Prayer",
    "Magic", "Cooking", "Woodcutting", "Fletching", "Fishing", "Firemaking",
    "Crafting", "Smithing", "Mining", "Herblore", "Agility", "Thieving",
    "Slayer", "Farming", "Runecrafting", "Hunter", "Construction", "Sailing"
]

class OSRS(commands.Cog):
    """Comando para buscar hiscores de OSRS."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="osrs",
        description="Busca os hiscores de um jogador de OSRS."
    )
    @app_commands.describe(
        username="Nome do jogador Old School RuneScape."
    )
    @app_commands.guilds(discord.Object(id=int(os.getenv("GUILD_ID"))))
    async def osrs(self, interaction: discord.Interaction, username: str):
        """Slash command /osrs para buscar hiscores."""
        await interaction.response.defer(thinking=True)

        try:
            async with aiohttp.ClientSession() as session:
                url = HISCORES_URL.format(username.replace(" ", "+"))
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send(f"❌ Jogador **{username}** não encontrado.")
                    data = await resp.text()
                    rows = data.splitlines()

            embed = discord.Embed(
                title=f"{username} Hiscores",
                color=discord.Color.gold()
            )

            for i, skill in enumerate(SKILLS):
                if i >= len(rows):
                    break
                level = rows[i].split(",")[1]
                embed.add_field(name=skill, value=level, inline=True)


            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao processar hiscores: `{e}`")

    @commands.hybrid_command(name="osrs")
    async def osrs_text(self, ctx: commands.Context, *, username: str):
        """Permite usar o comando via texto, ex: !osrs Zezima"""
        class DummyInteraction:
            def __init__(self, ctx):
                self.ctx = ctx

            @property
            def response(self):
                return self

            async def defer(self, thinking=True):
                await self.ctx.send("⏳ A buscar hiscores...")

            async def followup(self, send=None, **kwargs):
                if send:
                    await self.ctx.send(send)
                elif "content" in kwargs:
                    await self.ctx.send(kwargs["content"])

            async def followup_send(self, content):
                await self.ctx.send(content)

        fake_interaction = DummyInteraction(ctx)
        await self.osrs.__func__(self, fake_interaction, username)

async def setup(bot: commands.Bot):
    await bot.add_cog(OSRS(bot))
