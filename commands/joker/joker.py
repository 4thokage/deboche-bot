import discord
from discord.ext import commands
from discord import app_commands
import asyncio, json, random
from .game import Question, GameState, PRIZES
from config import GUILD_ID

class JokerView(discord.ui.View):
    def __init__(self, cog, state: GameState, timeout: int):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.state = state

        for idx, letter in enumerate("ABCD"):
            self.add_item(self.AnswerButton(cog, state, idx, letter))
        self.add_item(self.JokerButton(cog, state))

    class AnswerButton(discord.ui.Button):
        def __init__(self, cog, state, idx, letter):
            super().__init__(label=letter, style=discord.ButtonStyle.primary)
            self.cog, self.state, self.idx = cog, state, idx

        async def callback(self, interaction: discord.Interaction):
            await self.cog.handle_answer(interaction, self.state, self.idx)

    class JokerButton(discord.ui.Button):
        def __init__(self, cog, state):
            super().__init__(label=f"🎭 Usar Joker ({state.jokers})", style=discord.ButtonStyle.secondary)
            self.cog, self.state = cog, state

        async def callback(self, interaction: discord.Interaction):
            if self.state.jokers <= 0:
                await interaction.response.send_message("Sem jokers!", ephemeral=True)
                return
            self.state.jokers -= 1
            wrong = [i for i in range(4) if i != self.state.active_question.correct]
            remove = random.choice(wrong)
            self.cog.hidden_options[self.state.user_id].append(remove)
            await interaction.response.edit_message(view=self.cog.build_view(self.state))

class JokerCog(commands.Cog):
    """Concurso JOKER 🇵🇹"""

    def __init__(self, bot):
        self.bot = bot
        self.states: dict[int, GameState] = {}
        self.hidden_options: dict[int, list[int]] = {}
        with open("commands/joker/questions_pt.json", encoding="utf8") as f:
            self.questions = [Question(**q) for q in json.load(f)]

    @app_commands.command(name="joker", description="Inicia o jogo JOKER")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def start(self, interaction: discord.Interaction):
        state = GameState(user_id=interaction.user.id)
        self.states[state.user_id] = state
        await self.next_question(interaction, state)

    async def next_question(self, target, state):
        q = random.choice(self.questions)
        state.active_question = q
        self.hidden_options[state.user_id] = []

        desc = "\n".join(f"{ltr}. {opt}" for ltr, opt in zip("ABCD", q.options))
        embed = discord.Embed(
            title=f"Pergunta {state.current_index + 1}",
            description=f"{q.text}\n\n{desc}",
            color=discord.Color.blue(),
        )

        timeout = 30 if state.current_index < 4 else 40 if state.current_index < 8 else 50
        view = JokerView(self, state, timeout)

        if isinstance(target, discord.Interaction):
            await target.response.send_message(embed=embed, view=view)
        else:  # legacy ctx
            await target.send(embed=embed, view=view)

    # optional: keep reference to the sent message if you need to edit later

    async def handle_answer(self, inter, state, choice):
        correct = choice == state.active_question.correct
        state.lose_jokers_or_levels(not correct)
        if correct:
            await inter.response.send_message("✅ Correto!", ephemeral=True)
        else:
            await inter.response.send_message("❌ Errado!", ephemeral=True)
        await self.after_answer(inter.channel, state)

    async def after_answer(self, ctx, state):
        state.current_index += 1
        if state.current_index >= len(PRIZES):
            prize = PRIZES[state.prize_level] if state.prize_level >= 0 else 0
            await ctx.send(f"🎉 Fim! Ganhou **{prize}€**")
            del self.states[state.user_id]
        else:
            await self.next_question(ctx, state)

async def setup(bot):
    await bot.add_cog(JokerCog(bot))