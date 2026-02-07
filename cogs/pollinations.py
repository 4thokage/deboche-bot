import os
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import urllib.parse
from config import POLLINATIONS_API_KEY
from config import GUILD_ID


POLLINATIONS_BASE_URL = "https://gen.pollinations.ai/image"


class Pollinations(commands.Cog):
    """Geração de imagens via Pollinations.ai"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_key = POLLINATIONS_API_KEY

        if not self.api_key:
            raise RuntimeError("❌ POLLINATIONS_API_KEY não definido no ambiente")

        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    @app_commands.command(
        name="bob_ross",
        description="Gera uma imagem com IA (Pollinations)"
    )
    @app_commands.describe(
        prompt="Descrição da imagem a gerar"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def image(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()

        # Encode do prompt para URL
        encoded_prompt = urllib.parse.quote(prompt)

        image_url = f"{POLLINATIONS_BASE_URL}/{encoded_prompt}?model=flux"

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            # Apenas para validar se a imagem é acessível
            async with self.session.get(image_url, headers=headers) as r:
                if r.status != 200:
                    raise Exception(f"Pollinations retornou {r.status}")

            embed = discord.Embed(
                title="🎨 Pollinations AI",
                description=f"**Prompt:** {prompt}",
                color=0x9B59B6
            )

            embed.set_image(url=image_url)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Erro ao gerar imagem: `{e}`"
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Pollinations(bot))
