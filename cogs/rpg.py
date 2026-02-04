import random
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import GUILD_ID


# =========================
# RPG COG
# =========================

class RPG(commands.Cog):
    """Sistema de leveling, economia, quests e PvP"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ======================
    # PERFIL
    # ======================
    @commands.hybrid_command(
        name="perfil_old",
        description="Mostra o teu perfil e settings, permite alterar alguns."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def perfil(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        user = user or ctx.author
        db = self.bot.database

        profile = await db.get_user(user.id)
        if not profile:
            profile = await db.create_user(user.id, user.display_name)

        embed = discord.Embed(
            title=f"Perfil de {user.display_name}",
            color=0x5865F2,
            description=f"**Level:** {await db.get_level(user.id)}\n"
                        f"**Coins:** {profile['coins']}\n"
                        f"**XP:** {profile['xp']}\n"
                        f"**Reputação:** {profile['reputation']}\n"
                        f"**Cervejas (comandos usados):** {profile['commands_count']}\n"
                        f"**Bio:** {profile['bio'] or '—'}"
        )
        embed.add_field(
            name="Settings",
            value=f"🌐 Language: {profile['language']}\n"
                  f"🔔 Notifications: {'On' if profile['notifications_enabled'] else 'Off'}\n"
                  f"🎵 Sound: {'On' if profile['sound_enabled'] else 'Off'}\n"
                  f"🌙 Dark Mode: {'On' if profile['dark_mode'] else 'Off'}"
        )
        await ctx.send(embed=embed, view=ProfileView(db, user.id))

    # ======================
    # DAILY / QUEST
    # ======================
    @commands.hybrid_command(
        name="daily",
        description="Recolhe recompensas diárias (XP e coins)."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def daily(self, ctx: commands.Context):
        db = self.bot.database
        xp = random.randint(5, 20)
        coins = random.randint(10, 50)
        await db.complete_quest(ctx.author.id, coins=coins, xp=xp)

        embed = discord.Embed(
            title="🎁 Recompensa diária",
            description=f"Recebeste **{coins} moedas** e **{xp} XP**!",
            color=0x57F287
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="quest",
        description="Completa uma quest aleatória para ganhar XP e coins."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def quest(self, ctx: commands.Context):
        db = self.bot.database
        quests = [
            ("Derrotar monstros na floresta", 10, 20),
            ("Salvar aldeões de bandidos", 15, 30),
            ("Explorar masmorras antigas", 20, 40),
            ("Caçar o dragão da montanha", 30, 50)
        ]
        quest = random.choice(quests)
        await db.complete_quest(ctx.author.id, coins=quest[2], xp=quest[1])

        embed = discord.Embed(
            title="🗡️ Quest Completa!",
            description=f"**{quest[0]}** concluída!\nGanhaste **{quest[2]} moedas** e **{quest[1]} XP**",
            color=0xF1C40F
        )
        await ctx.send(embed=embed)

    # ======================
    # PvP BATTLES
    # ======================
    @commands.hybrid_command(
        name="pvp",
        description="Desafia outro jogador para um combate PvP!"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def pvp(self, ctx: commands.Context, opponent: discord.Member):
        db = self.bot.database
        if opponent.id == ctx.author.id:
            return await ctx.send("Não podes lutar contigo mesmo!")

        battle = await db.pvp_battle(ctx.author.id, opponent.id)
        if "error" in battle:
            return await ctx.send(battle["error"])

        if battle["winner"] is None:
            result = "🤝 Empate!"
        else:
            winner = ctx.guild.get_member(int(battle["winner"]))
            loser = ctx.guild.get_member(int(battle["loser"]))
            result = f"🏆 **{winner.display_name}** venceu contra **{loser.display_name}**!\n"
            result += f"🎁 Recebeu {battle['reward_coins']} moedas e {battle['reward_xp']} XP"

        embed = discord.Embed(
            title="⚔️ PvP Battle",
            description=result + f"\n\nAtaques: {ctx.author.display_name}={battle['attack1']} | "
                                  f"{opponent.display_name}={battle['attack2']}",
            color=0xE74C3C
        )
        await ctx.send(embed=embed)

    # ======================
    # LEADERBOARD
    # ======================
    @commands.hybrid_command(
        name="leaderboard",
        description="Mostra os top users por coins ou XP"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def leaderboard(self, ctx: commands.Context, type: Optional[str] = "xp"):
        db = self.bot.database
        type = type.lower()
        if type not in ["xp", "coins"]:
            type = "xp"

        async with db.connection.execute(
            f"SELECT discord_id, name, {type} FROM users ORDER BY {type} DESC LIMIT 10"
        ) as cursor:
            rows = await cursor.fetchall()

        description = ""
        for i, row in enumerate(rows, start=1):
            member = ctx.guild.get_member(int(row[0]))
            name = member.display_name if member else row[1]
            description += f"**{i}. {name}** — {row[2]} {type.upper()}\n"

        embed = discord.Embed(
            title=f"🏅 Top 10 por {type.upper()}",
            description=description or "Sem dados.",
            color=0xFFD700
        )
        await ctx.send(embed=embed)
        


class EditProfileModal(discord.ui.Modal, title="Editar Perfil"):
    bio = discord.ui.TextInput(label="Bio", required=False, max_length=200)
    zone = discord.ui.TextInput(label="Zona", required=False, max_length=50)
    position = discord.ui.TextInput(label="Posição", required=False, max_length=50)

    def __init__(self, db, user_id):
        super().__init__()
        self.db = db
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        await self.db.connection.execute(
            """
            UPDATE users
            SET bio=?, zone=?, position=?
            WHERE discord_id=?
            """,
            (self.bio.value, self.zone.value, self.position.value, str(self.user_id))
        )
        await self.db.connection.commit()
        await interaction.response.send_message("✅ Perfil atualizado!", ephemeral=True)
        
class ProfileView(discord.ui.View):
    def __init__(self, db, user_id):
        super().__init__(timeout=120)
        self.db = db
        self.user_id = user_id

    @discord.ui.button(label="Editar Perfil", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "❌ Só podes editar o teu perfil.", ephemeral=True
            )

        await interaction.response.send_modal(
            EditProfileModal(self.db, self.user_id)
        )
# =========================
# SETUP
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(RPG(bot))