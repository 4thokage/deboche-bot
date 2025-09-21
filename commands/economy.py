import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from config import GUILD_ID
import random

COOLDOWNS = {
    "work": 86400,  # 1 dia em segundos
    "pedir": 300    # 5 minutos
}

user_cooldowns = {}  # dict[user_id][command] = timestamp

class Economy(commands.Cog):
    """Economy commands: coins, work, slots, gifts"""

    def __init__(self, bot):
        self.bot = bot
        self.queue: List[Tuple[int, str]] = []

    # ------------------------
    # Work
    # ------------------------
    @app_commands.command(
        name="trabalhar",
        description="Ganha coins fazendo um trabalho"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def work(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        db = self.bot.db
        db.ensure_user(user_id)

        # Cooldown
        last_used = user_cooldowns.get(user_id, {}).get("work")
        now_ts = datetime.utcnow().timestamp()
        if last_used and now_ts - last_used < COOLDOWNS["work"]:
            remaining = int(COOLDOWNS["work"] - (now_ts - last_used))
            await interaction.response.send_message(
                f"⏳ Só podes trabalhar de novo em {remaining//3600}h {(remaining%3600)//60}m", 
                ephemeral=True
            )
            return

        # Random coins
       
        earned = random.randint(50, 200)
        user_row = db.get_user(user_id)
        print(dict(user_row))
        user = dict(user_row) if user_row else {}
        cur_coins = user.get("coins")
        db.update_profile(user_id, coins=cur_coins + earned)

        # Update cooldown
        user_cooldowns.setdefault(user_id, {})["work"] = now_ts

        await interaction.response.send_message(f"💼 Trabalhaste e ganhaste **{earned} coins**!")

    # ------------------------
    # Carteira
    # ------------------------
    @app_commands.command(
        name="carteira",
        description="Mostra o dinheiro do jogador"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def carteira(self, interaction: discord.Interaction):
        """Exibe a carteira e inventário do jogador"""
        await interaction.response.defer()

        user_id = str(interaction.user.id)
        db = self.bot.db
        db.ensure_user(user_id)
        
        user_data = db.get_user(user_id)
        coins = user_data["coins"]

        inventario = db.get_inventory(user_id)

        if not inventario:
            descricao = "Não tens nenhum item no inventário."
        else:
            linhas = []
            for item in inventario:
                linha = f"**{item['item']}** x{item['qty']}"
                if item["selling"]:
                    linha += f" - 💰 {item['price']} coins"
                linhas.append(linha)
            descricao = "\n".join(linhas)

        embed = discord.Embed(
            title=f"Inventário de {interaction.user.display_name}",
            description=f"💰 Coins: {coins}\n\n{descricao}",
            color=0x2F3136
        )

        await interaction.followup.send(embed=embed)


    # ------------------------
    # Dar coins
    # ------------------------
    @app_commands.command(
        name="dar",
        description="Dá coins a outro jogador"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(user="O jogador a quem dar coins", amount="Quantidade de coins")
    async def dar(self, interaction: discord.Interaction, user: discord.User, amount: int):
        giver_id = str(interaction.user.id)
        receiver_id = str(user.id)
        db = self.bot.db

        if amount <= 0:
            await interaction.response.send_message("❌ Quantidade inválida", ephemeral=True)
            return

        db.ensure_user(giver_id)
        db.ensure_user(receiver_id)

        giver = db.get_user(giver_id)
        if giver["coins"] < amount:
            await interaction.response.send_message("❌ Não tens coins suficientes", ephemeral=True)
            return

        db.update_profile(giver_id, coins=giver["coins"] - amount)
        receiver = db.get_user(receiver_id)
        db.update_profile(receiver_id, coins=receiver["coins"] + amount)

        await interaction.response.send_message(f"✅ Deste **{amount} coins** a {user.mention}.")

    # ------------------------
    # Pedir coins
    # ------------------------
    @app_commands.command(
        name="pedir",
        description="Pede coins a chance aleatória"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def pedir(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        db = self.bot.db
        db.ensure_user(user_id)

        last_used = user_cooldowns.get(user_id, {}).get("pedir")
        now_ts = datetime.utcnow().timestamp()
        if last_used and now_ts - last_used < COOLDOWNS["pedir"]:
            remaining = int(COOLDOWNS["pedir"] - (now_ts - last_used))
            await interaction.response.send_message(
                f"⏳ Só podes pedir coins de novo em {remaining//60}m", 
                ephemeral=True
            )
            return

        import random
        earned = random.choice([0, 1, 2, 5, 10, 15])
        cur_coins = db.get_user(user_id)["coins"]
        db.update_profile(user_id, coins=cur_coins + earned)
        user_cooldowns.setdefault(user_id, {})["pedir"] = now_ts

        if earned == 0:
            await interaction.response.send_message("❌ Ninguém te deu coins 😢")
        else:
            await interaction.response.send_message(f"💸 Recebeste **{earned} coins**.")

    # ------------------------
    # Slot machine
    # ------------------------
    @app_commands.command(
        name="slot",
        description="Aposta coins numa slot machine"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(amount="Quantidade de coins para apostar")
    async def slot(self, interaction: discord.Interaction, amount: int):
        import random
        user_id = str(interaction.user.id)
        db = self.bot.db
        db.ensure_user(user_id)
        user = db.get_user(user_id)

        if amount <= 0 or amount > user["coins"]:
            await interaction.response.send_message("❌ Quantidade inválida ou coins insuficientes", ephemeral=True)
            return

        symbols = ["🍒","🍋","🍊","🍉","⭐","💎"]
        result = [random.choice(symbols) for _ in range(3)]
        multiplier = 0
        if result[0] == result[1] == result[2]:
            multiplier = 5
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            multiplier = 2

        win = amount * multiplier
        db.update_profile(user_id, coins=user["coins"] - amount + win)

        await interaction.response.send_message(f"🎰 {' '.join(result)}\n💰 Ganhaste {win} coins!")

    @app_commands.command(
        name="cenas",
        description="Vê a queue ou compra algo para entrar nela."
    )
    @app_commands.describe(comprar="Texto a associar ao teu nome na queue")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def cenas(self, interaction: discord.Interaction, comprar: str | None = None):
        user_id = interaction.user.id

        if comprar:
            # Adiciona o user + texto à queue
            self.queue.append((user_id, comprar))
            return await interaction.response.send_message(
                f"✅ {interaction.user.mention} adicionou **{comprar}** à queue!"
            )

        # Mostrar queue
        if not self.queue:
            return await interaction.response.send_message("📭 A queue está vazia.")

        linhas = []
        for idx, (uid, item) in enumerate(self.queue, start=1):
            linhas.append(f"{idx}. <@{uid}> — {item}")

        embed = discord.Embed(
            title="📜 Queue atual",
            description="\n".join(linhas),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
async def setup(bot):
    await bot.add_cog(Economy(bot))
