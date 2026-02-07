import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import glob
from config import GUILD_ID

class CogGenerator(commands.Cog):
    """Cria novos cogs automaticamente usando AI local, replicando o estilo do bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, "session"):
            bot.session = aiohttp.ClientSession()

        # Pasta dos cogs
        self.cogs_folder = "cogs"
        
    def get_example_cog(self) -> str:
      """Pega apenas o cog anime.py como exemplo para o prompt da AI."""
      filename = os.path.join(self.cogs_folder, "anime.py")
      if not os.path.exists(filename):
          return ""  # fallback vazio se não existir
      with open(filename, "r", encoding="utf-8") as f:
          return f.read()


    @commands.hybrid_command(
        name="create_cog",
        description="Cria um cog automaticamente replicando a estrutura atual"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def create_cog(self, ctx: commands.Context, *, description: str):
        await ctx.defer()

        example_cog = self.get_example_cog()
        prompt = f"""
          You are a Python expert and a Discord bot developer.
          Create a discord.py cog based on the following example:

          EXAMPLE COG:
          {example_cog}

          Now, create a new cog with this functionality:
          {description}

          Rules:
          - Follow the exact same import style and setup as the example.
          - Class name must be unique.
          - Include async def setup(bot) to load the cog.
          - Only output Python code, nothing else.
          - Make it ready to save as a .py file.
          """
        # Chamada à AI local
        async with self.bot.session.post(
            "http://localhost:11434/api/generate",
            json={
                "prompt": prompt,
                "model": "qwen3:8b",
                "stream": False,
                "options": {"temperature": 0.7}
            }
        ) as resp:
            if resp.status != 200:
                return await ctx.send(f"Erro AI: {resp.status}")
            data = await resp.json()
            code = data.get("response")

        # Gera nome único
        filename = os.path.join(
            self.cogs_folder,
            f"generated_{int(ctx.message.id if ctx.message else ctx.id)}.py"
        )

        # Validação básica do Python
        try:
            compile(code, filename, "exec")
        except Exception as e:
            return await ctx.send(f"Erro no código gerado: {e}")

        # Salva o arquivo
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        # Carrega cog
        try:
            await self.bot.load_extension(f"{self.cogs_folder}.{os.path.basename(filename)[:-3]}")
            await ctx.send(f"Cog criado e carregado com sucesso: `{filename}`")
        except Exception as e:
            await ctx.send(f"Erro ao carregar cog: {e}")

async def setup(bot) -> None:
    await bot.add_cog(CogGenerator(bot))