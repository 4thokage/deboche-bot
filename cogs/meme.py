import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
from config import GUILD_ID

class MemeGen(commands.Cog):
    """Gera memes com texto custom"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="meme-gen",
        description="Cria um meme com texto superior e inferior"
    )
    @app_commands.describe(
        top="Texto no topo",
        bottom="Texto no fundo"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def meme_gen(self, interaction: discord.Interaction, top: str, bottom: str):
        await interaction.response.defer()

        # URL de imagem base (podes trocar para qualquer meme clássico)
        base_url = "https://i.imgflip.com/1bij.jpg"  # exemplo do meme 'Distracted Boyfriend'

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as resp:
                if resp.status != 200:
                    return await interaction.followup.send("❌ Não consegui carregar a imagem base.")
                image_data = await resp.read()

        image = Image.open(io.BytesIO(image_data))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", size=90)  # pode ser outra fonte disponível

        # Texto no topo e fundo
        draw.text((10, 10), top, fill="white", stroke_width=2, stroke_fill="black", font=font)
        draw.text((10, image.height - 100), bottom, fill="white", stroke_width=2, stroke_fill="black", font=font)


        # Salvar em memória
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)

        file = discord.File(buf, filename="meme.png")
        await interaction.followup.send(file=file)


async def setup(bot):
    await bot.add_cog(MemeGen(bot))