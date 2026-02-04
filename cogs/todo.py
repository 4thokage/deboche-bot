import json
import os
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands import Context

from config import GUILD_ID

DATA_FILE = "bot_todos.json"


# ---------- Storage helpers ----------
def load_todos() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_todos(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------- Cog ----------
class Todo(commands.Cog):
    """Lista de TODOs pessoais"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(
        name="todo",
        description="Gerir a tua lista de TODOs",
        invoke_without_command=True
    )
    async def todo(self, ctx: Context):
        await ctx.send("📝 Usa `/todo add`, `/todo list`, `/todo done` ou `/todo remove`")

    # -------- ADD --------
    @todo.command(name="add", description="Adicionar um TODO")
    async def add(self, ctx: Context, *, text: str):
        todos = load_todos()
        user_id = str(ctx.author.id)

        todos.setdefault(user_id, [])

        todos[user_id].append({
            "text": text,
            "done": False,
            "created_at": datetime.utcnow().isoformat()
        })

        save_todos(todos)
        await ctx.send(f"✅ TODO adicionado:\n> {text}")

    # -------- LIST --------
    @todo.command(name="list", description="Listar os teus TODOs")
    async def list_(self, ctx: Context):
        todos = load_todos()
        user_id = str(ctx.author.id)

        user_todos = todos.get(user_id, [])
        if not user_todos:
            await ctx.send("📭 Não tens TODOs.")
            return

        embed = discord.Embed(
            title="📝 Os teus TODOs",
            color=0x2ECC71
        )

        for i, todo in enumerate(user_todos, start=1):
            status = "✅" if todo["done"] else "⏳"
            embed.add_field(
                name=f"{i}. {status}",
                value=todo["text"],
                inline=False
            )

        await ctx.send(embed=embed)

    # -------- DONE --------
    @todo.command(name="done", description="Marcar um TODO como feito")
    async def done(self, ctx: Context, index: int):
        todos = load_todos()
        user_id = str(ctx.author.id)

        user_todos = todos.get(user_id)
        if not user_todos or index < 1 or index > len(user_todos):
            await ctx.send("❌ TODO inválido.")
            return

        user_todos[index - 1]["done"] = True
        save_todos(todos)

        await ctx.send(f"🎉 TODO #{index} marcado como feito!")

    # -------- REMOVE --------
    @todo.command(name="remove", description="Remover um TODO")
    async def remove(self, ctx: Context, index: int):
        todos = load_todos()
        user_id = str(ctx.author.id)

        user_todos = todos.get(user_id)
        if not user_todos or index < 1 or index > len(user_todos):
            await ctx.send("❌ TODO inválido.")
            return

        removed = user_todos.pop(index - 1)
        save_todos(todos)

        await ctx.send(f"🗑️ TODO removido:\n> {removed['text']}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Todo(bot))