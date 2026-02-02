import aiohttp
import asyncio
import json
import discord
from discord.ext import commands
from discord import app_commands
from config import GUILD_ID


class OllamaCog(commands.Cog):
    """Interact with local Ollama API"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_url = "http://localhost:11434/api/generate"

    @app_commands.command(name="qwen", description="Ask qwen AI something!")
    @app_commands.describe(prompt="The question or prompt to ask qwen")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ollama(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()  # defer for streaming/editing

        payload = {
            "prompt": prompt,
            "model": "qwen3:8b",
            "stream": True,
            "options": {
                "temperature": 0.7
            }
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api_url, json=payload) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send(
                            f"Error: {resp.status} {await resp.text()}"
                        )

                    # initial message
                    message = await interaction.followup.send("💬 Ollama is thinking...")

                    full_response = ""

                    async for line_bytes in resp.content:
                        if not line_bytes:
                            continue
                        line = line_bytes.decode("utf-8").strip()
                        if not line:
                            continue

                        # Each line might be JSON
                        try:
                            data = json.loads(line)
                            if "thinking" in data:
                                chunk = data["thinking"]
                                full_response += chunk
                                try:
                                    await message.edit(content=full_response)
                                    await asyncio.sleep(0.05)
                                except discord.HTTPException:
                                    pass
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            # sometimes the API may send partial lines
                            continue

            except aiohttp.ClientError as e:
                await interaction.followup.send(f"Failed to contact Ollama: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(OllamaCog(bot))