import random
import asyncio
import datetime
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Context

from config import GUILD_ID


# ======================
# UTILS
# ======================

def closest_smaller(d: dict, key: int):
    for k in sorted(d.keys(), reverse=True):
        if key >= k:
            return d[k]
    return ""


# ======================
# UI COMPONENTS
# ======================

class CoinFlipView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)
        self.choice = None

    @discord.ui.button(label="Cara", emoji="🪙", style=discord.ButtonStyle.primary)
    async def cara(self, interaction: discord.Interaction, _):
        self.choice = "cara"
        self.stop()

    @discord.ui.button(label="Coroa", emoji="🪙", style=discord.ButtonStyle.primary)
    async def coroa(self, interaction: discord.Interaction, _):
        self.choice = "coroa"
        self.stop()


class RPSSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Escolhe a tua jogada",
            options=[
                discord.SelectOption(label="Pedra", emoji="🪨"),
                discord.SelectOption(label="Papel", emoji="🧻"),
                discord.SelectOption(label="Tesoura", emoji="✂️"),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        user = self.values[0].lower()
        bot = random.choice(["pedra", "papel", "tesoura"])

        rules = {
            ("pedra", "tesoura"),
            ("tesoura", "papel"),
            ("papel", "pedra"),
        }

        if user == bot:
            result = "🤝 **Empate!**"
            color = 0xF59E42
        elif (user, bot) in rules:
            result = "🎉 **Ganhaste!**"
            color = 0x57F287
        else:
            result = "💀 **Perdeste!**"
            color = 0xE02B2B

        embed = discord.Embed(
            title="Pedra Papel Tesoura",
            description=f"{result}\n\nTu: **{user}**\nBot: **{bot}**",
            color=color,
        )

        await interaction.response.edit_message(embed=embed, view=None)


class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=20)
        self.add_item(RPSSelect())


# ======================
# 🍪 BOLACHA GAME
# ======================

class CookieGame(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=10)
        self.start = datetime.datetime.utcnow()
        self.winner = None

    @discord.ui.button(label="🍪 APANHAR!", style=discord.ButtonStyle.success)
    async def catch(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.winner:
            return

        self.winner = interaction.user
        delta = (datetime.datetime.utcnow() - self.start).total_seconds()

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="🎉 BOLACHA APANHADA!",
            description=f"**{interaction.user.display_name}** reagiu em **{delta:.3f}s**",
            color=0x57F287,
        )

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


# ======================
# COG
# ======================

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- FACTO ----------
    @commands.hybrid_command(name="facto", description="Obtem um facto aleatório.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def facto(self, ctx: Context):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://uselessfacts.jsph.pl/random.json?language=pt") as r:
                data = await r.json()
        await ctx.send(embed=discord.Embed(description=data["text"], color=0x9B59B6))

    # ---------- MOEDA ----------
    @commands.hybrid_command(name="moeda", description="Cara ou coroa")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def moeda(self, ctx: Context):
        view = CoinFlipView()
        msg = await ctx.send("🪙 **Escolhe:**", view=view)
        await view.wait()

        if not view.choice:
            return await msg.edit(content="⌛ Tempo esgotado!", view=None)

        result = random.choice(["cara", "coroa"])
        win = view.choice == result

        await msg.edit(
            content=f"Resultado: **{result}**\n"
                    f"{'🎉 Ganhaste!' if win else '💀 Perdeste!'}",
            view=None,
        )

    # ---------- RPS ----------
    @commands.hybrid_command(name="rps", description="Pedra papel tesoura")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def rps(self, ctx: Context):
        await ctx.send("🎮 Escolhe a jogada:", view=RPSView())

    # ---------- BOLACHA ----------
    @commands.hybrid_command(name="bolacha", description="Jogo de reação 🍪")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def bolacha(self, ctx: Context):
        msg = await ctx.send("🍪 A bolacha vai cair... fica atento!")

        # fintas
        for _ in range(random.randint(2, 5)):
            await asyncio.sleep(random.uniform(0.8, 1.5))
            await msg.edit(content="👀 Quase...")

        await asyncio.sleep(random.uniform(1.5, 3))
        view = CookieGame()
        view.start = datetime.datetime.utcnow()

        await msg.edit(
            content="🔥 **AGORA!**",
            embed=discord.Embed(
                title="🍪 APANHA A BOLACHA!",
                description="Primeiro clique ganha",
                color=0xE67E22,
            ),
            view=view,
        )

    # ---------- PENIS ----------
    @commands.hybrid_command(name="penis", description="Tamanho totalmente científico™")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def penis(self, ctx: Context, membro: discord.Member = None):
        membro = membro or ctx.author
        size = random.randint(0, 30)

        comments = {
            0: "😅 complicado",
            6: "meh",
            12: "ok",
            18: "👀 respeitável",
            25: "😳 cuidado",
        }

        embed = discord.Embed(
            title=f"Pénis de {membro.display_name}",
            description=f"8{'=' * size}D",
            color=0x2F3136,
        )
        embed.set_footer(text=closest_smaller(comments, size))
        await ctx.send(embed=embed)

    # ---------- BOLA ----------
    @commands.hybrid_command(name="bola", description="Bola de cristal 🎱")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def bola(self, ctx: Context, pergunta: str):
        respostas = [
            "Sim.", "Não.", "Talvez.", "Pergunta depois.",
            "Muito provável.", "Nem penses nisso.",
        ]
        await ctx.send(
            embed=discord.Embed(
                title="🎱 Bola de Cristal",
                description=f"**Pergunta:** {pergunta}\n**Resposta:** {random.choice(respostas)}",
                color=0x5865F2,
            )
        )
    async def fetch_gif(self, answer: str) -> str:
        url = f"https://yesno.wtf/api?force={answer}"
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise RuntimeError("API yesno.wtf falhou")
                data = await resp.json()
                return data["image"]

    @commands.hybrid_command(name="sim", description="Resposta SIM (GIF)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def sim(self, ctx: commands.Context):
        try:
            gif_url = await self.fetch_gif("yes")
            await ctx.send(gif_url)
        except Exception:
            await ctx.send("❌ O universo não conseguiu decidir (sim).")

    @commands.hybrid_command(name="nao", description="Resposta NÃO (GIF)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def nao(self, ctx: commands.Context):
        try:
            gif_url = await self.fetch_gif("no")
            await ctx.send(gif_url)
        except Exception:
            await ctx.send("❌ O universo não conseguiu decidir (não).")

    @commands.hybrid_command(name="owen_wilson")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def owen_wilson(self, ctx: commands.Context):
        url = "https://owen-wilson-wow-api.onrender.com/wows/random"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return await ctx.send("Failed to fetch a wow 😢")
                data = await resp.json()
        
        if not data or len(data) == 0:
            return await ctx.send("No wow found 😢")

        wow = data[0]  # API returns a list with a single dict

        embed = discord.Embed(
            title=f"{wow['movie']} ({wow['year']})",
            description=f"**Character:** {wow['character']}\n**Director:** {wow['director']}\n**Timestamp:** {wow['timestamp']}\n**Line:** {wow['full_line']}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=wow['poster'])
        embed.add_field(name="Movie Duration", value=wow['movie_duration'])
        embed.add_field(name="Wow Count", value=f"{wow['current_wow_in_movie']} of {wow['total_wows_in_movie']}")
        embed.add_field(name="Video 1080p", value=f"[Click Here]({wow['video']['1080p']})", inline=False)
        embed.add_field(name="Audio", value=f"[Click Here]({wow['audio']})", inline=False)

        await ctx.send(embed=embed)
        
    @app_commands.command(name="shrek", description="Get a random Shrek quote")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def shrek(self, interaction: discord.Interaction):
        url = "https://shrekofficial.com/quotes/random"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await interaction.response.send_message("Failed to fetch a Shrek quote 😢", ephemeral=True)
                    return
                text = await resp.text()
        
        # Format the text in a code block to preserve line breaks
        embed = discord.Embed(
            title="🟢 Random Shrek Quote",
            description=f"```\n{text}\n```",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)
# ======================
# SETUP
# ======================

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))