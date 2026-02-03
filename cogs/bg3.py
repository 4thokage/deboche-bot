import os
import json
import random
from datetime import datetime, timedelta
import asyncio

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Context
from config import GUILD_ID

DATA_FILE = "quem_joga_hoje.json"

def load_players():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_players(players):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

def parse_time_string(time_str: str):
    """Parse a HH:MM string into a datetime.time object."""
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return None

def compute_shared_time(players):
    """
    Compute overlapping time window for all players.
    Each player is a dict with 'start' and 'end' keys (HH:MM strings).
    Returns (start_datetime, end_datetime) or None if no overlap.
    """
    if not players:
        return None
    
    # Convert strings to datetime objects today
    today = datetime.now().date()
    intervals = []
    for p in players:
        start = datetime.combine(today, parse_time_string(p["start_time"]))
        end = datetime.combine(today, parse_time_string(p["end_time"]))
        intervals.append((start, end))
    
    # Find the latest start and earliest end
    latest_start = max(i[0] for i in intervals)
    earliest_end = min(i[1] for i in intervals)
    
    if latest_start >= earliest_end:
        return None
    return latest_start, earliest_end

class Bg3Utility(commands.Cog, name="bg3_utilities"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.reminders = {}  # {user_id: task}
    
    @commands.hybrid_command(
        name="quem_joga",
        description="Marca quem joga hoje com horário e objetivos"
    )
    @app_commands.describe(
        nome_jogo="Nome do jogo",
        objetivos="Objetivos da sessão",
        start_time="Hora de início (HH:MM)",
        end_time="Hora de fim (HH:MM)"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def quem_joga(
        self, context: Context,
        nome_jogo: str = None,
        objetivos: str = None,
        start_time: str = None,
        end_time: str = None
    ) -> None:
        """
        Marca o utilizador com horários individuais e objetivos.
        """
        players = load_players()
        user_id = str(context.author.id)
        user_name = context.author.display_name

        # Validate times
        if start_time and end_time:
            start_obj = parse_time_string(start_time)
            end_obj = parse_time_string(end_time)
            if not start_obj or not end_obj or start_obj >= end_obj:
                await context.send("⛔ Horário inválido! Use HH:MM e start < end.")
                return
        else:
            start_time = None
            end_time = None

        # Update or add user
        existing = next((p for p in players if p["id"] == user_id), None)
        if existing:
            existing.update({
                "name": user_name,
                "start_time": start_time,
                "end_time": end_time,
                "nome_jogo": nome_jogo,
                "objetivos": objetivos
            })
        else:
            players.append({
                "id": user_id,
                "name": user_name,
                "start_time": start_time,
                "end_time": end_time,
                "nome_jogo": nome_jogo,
                "objetivos": objetivos
            })
        
        save_players(players)

        # Compute shared slot
        shared_slot = compute_shared_time(players)
        if shared_slot:
            shared_text = f"{shared_slot[0].strftime('%H:%M')} - {shared_slot[1].strftime('%H:%M')}"
        else:
            shared_text = "❌ Sem horário comum entre todos os jogadores"

        embed = discord.Embed(
            title="🎮 Quem joga hoje?",
            color=0x00FF00
        )

        description_lines = []
        for p in players:
            line = f"• {p['name']}"
            if p["start_time"] and p["end_time"]:
                line += f" ({p['start_time']} - {p['end_time']})"
            if p["nome_jogo"]:
                line += f" | Jogo: {p['nome_jogo']}"
            if p["objetivos"]:
                line += f" | Objetivos: {p['objetivos']}"
            description_lines.append(line)
        embed.description = "\n".join(description_lines)

        embed.set_footer(text=f"Horário comum: {shared_text} | Use /reset_jogo para limpar a lista")

        await context.send(embed=embed)

        # Schedule reminders 5 minutes before shared slot
        if shared_slot:
            reminder_time = shared_slot[0] - timedelta(minutes=5)
            if reminder_time > datetime.now():
                if user_id in self.reminders:
                    self.reminders[user_id].cancel()
                self.reminders[user_id] = self.bot.loop.create_task(
                    self.remind_user(context.author, reminder_time)
                )

    async def remind_user(self, user, remind_at):
        """Sends a reminder DM to the user at remind_at datetime."""
        wait_seconds = (remind_at - datetime.now()).total_seconds()
        await asyncio.sleep(wait_seconds)
        try:
            await user.send(f"⏰ Lembrete: Sua sessão de jogo começa em 5 minutos!")
        except discord.Forbidden:
            # Can't DM user
            pass

    @commands.hybrid_command(
        name="reset_jogo",
        description="Limpa a lista de quem joga hoje"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def reset_jogo(self, context: Context) -> None:
        save_players([])
        # Cancel scheduled reminders
        for task in self.reminders.values():
            task.cancel()
        self.reminders.clear()

        embed = discord.Embed(
            description="🧹 Lista limpa. Bora marcar outra sessão!",
            color=0x00FF00
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="d20",
        description="Rola um d20 para decisões rápidas"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def d20(self, context: Context) -> None:
        value = random.randint(1, 20)
        embed = discord.Embed(
            title="🎲 Resultado do d20",
            description=f"**{context.author.display_name} rolou:** **{value}**",
            color=0xFFD700
        )
        if value == 20:
            embed.set_footer(text="🔥 SUCESSO CRÍTICO 🔥")
        elif value == 1:
            embed.set_footer(text="💀 FALHA CRÍTICA 💀")
        await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Bg3Utility(bot))