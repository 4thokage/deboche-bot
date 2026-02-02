import os
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from config import GUILD_ID
from paginator import EmbedPaginator

GROQ_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

STRATEGY_PROMPT = """
Tu és o StrategyMaster, um estratega frio, lógico e experiente.
Pensa como um general, fundador ou líder tático.

Responde SEM conversa inútil e usa EXATAMENTE este formato:

🎯 OBJETIVO
(resumo claro)

🧠 ESTRATÉGIA PRINCIPAL
(passos numerados)

⚔️ ALTERNATIVA
(plano secundário caso algo falhe)

⚠️ RISCOS
(bullets curtos)

📊 MÉTRICAS
(como medir sucesso)

⏱️ TIMELINE
(curto / médio / longo prazo)

Não faças perguntas.
"""

class StrategyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="estrategia",
        description="Gera um plano estratégico baseado em objetivo, recursos e tempo"
    )
    @app_commands.describe(
        objetivo="Objetivo final",
        recursos="Recursos disponíveis",
        tempo="Tempo disponível"
    )
    @app_commands.guilds(discord.Object(GUILD_ID))
    async def estrategia(
        self,
        interaction: discord.Interaction,
        objetivo: str,
        recursos: str,
        tempo: str
    ):
        await interaction.response.defer(thinking=True)

        if not GROQ_KEY:
            return await interaction.followup.send(
                "❌ GROQ_API_KEY não está configurada."
            )

        prompt = f"""
{STRATEGY_PROMPT}

Objetivo: {objetivo}
Recursos: {recursos}
Tempo: {tempo}
"""

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 1200
        }

        headers = {
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GROQ_URL,
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        return await interaction.followup.send(
                            f"❌ Erro {resp.status} da API:\n{text[:400]}"
                        )
                    data = await resp.json()
        except Exception as e:
            return await interaction.followup.send(
                f"❌ Falha na requisição: `{e}`"
            )

        try:
            reply = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            reply = "⚠️ A IA não retornou resposta válida."

        paginator = EmbedPaginator(
            reply,
            title="🧠⚔️ StrategyMaster — Plano Estratégico",
            color=discord.Color.dark_gold()
        )
        await paginator.start(interaction)

async def setup(bot: commands.Bot):
    await bot.add_cog(StrategyCog(bot))
