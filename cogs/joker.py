import discord
from discord.ext import commands
from discord import app_commands
import asyncio, random, aiohttp
from dataclasses import dataclass
from typing import List, Optional
from config import GUILD_ID

# -------------------- Game Data --------------------

PRIZES = [50, 250, 500, 1000, 2500, 5000, 10000, 25000, 75000]

@dataclass
class Question:
    text: str
    options: List[str]   # exactly 4
    correct: int         # index 0..3

    @classmethod
    def from_api(cls, data: dict):
        """Build a Question from the-trivia-api.com response"""
        text = data["question"]["text"]
        correct_answer = data["correctAnswer"]
        options = data["incorrectAnswers"] + [correct_answer]
        random.shuffle(options)
        correct_index = options.index(correct_answer)
        return cls(text=text, options=options, correct=correct_index)

@dataclass
class GameState:
    user_id: int
    jokers: int = 7
    current_index: int = 0
    prize_level: int = -1  # -1 before 1st
    super_joker_used: bool = False
    active_question: Optional[Question] = None
    em_portugues: bool = True

    def lose_jokers_or_levels(self, wrong: bool):
        if not wrong:
            self.prize_level += 1
            return
        if self.jokers >= 3:
            self.jokers -= 3
        elif self.jokers == 2:
            self.jokers = 0
            self.prize_level -= 1
        elif self.jokers == 1:
            self.jokers = 0
            self.prize_level -= 2
        else:
            self.prize_level -= 3
        self.prize_level = max(self.prize_level, -1)

# -------------------- View --------------------

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
            # refresh question with hidden option
            await interaction.response.edit_message(
                embed=self.cog.build_embed(self.state),
                view=self.cog.build_view(self.state)
            )

# -------------------- Cog --------------------

class JokerCog(commands.Cog):
    """Concurso JOKER 🇵🇹"""

    def __init__(self, bot):
        self.bot = bot
        self.states: dict[int, GameState] = {}
        self.hidden_options: dict[int, list[int]] = {}

    # -------------------- API --------------------

    async def fetch_question(self, em_portugues: bool) -> Question:
        url = "https://the-trivia-api.com/v2/questions/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        q = Question.from_api(data[0])

        # If translation requested
        if em_portugues:
            q.text = await self.translate(q.text)
            q.options = [await self.translate(opt) for opt in q.options]

        return q

    async def translate(self, text: str) -> str:
        """Use LibreTranslate to translate"""
        url = "https://api.mymemory.translated.net/get?q="+text+"&langpair=en|pt"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("translatedText", text)
        return text

    # -------------------- Commands --------------------

    @app_commands.command(name="joker", description="Inicia o jogo JOKER")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def start(self, interaction: discord.Interaction, em_portugues: bool = False):
        state = GameState(user_id=interaction.user.id, em_portugues=em_portugues)
        self.states[state.user_id] = state
        await self.next_question(interaction, state)

    # -------------------- Helpers --------------------

    def build_view(self, state: GameState) -> JokerView:
        timeout = 30 if state.current_index < 4 else 40 if state.current_index < 8 else 50
        return JokerView(self, state, timeout)

    def build_embed(self, state: GameState) -> discord.Embed:
        q = state.active_question
        hidden = set(self.hidden_options[state.user_id])
        desc = "\n".join(
            f"{ltr}. {opt}" if idx not in hidden else f"~~{ltr}.~~ ❌"
            for idx, (ltr, opt) in enumerate(zip("ABCD", q.options))
        )
        return discord.Embed(
            title=f"Pergunta {state.current_index + 1}",
            description=f"{q.text}\n\n{desc}",
            color=discord.Color.blue(),
        )

    async def next_question(self, target, state: GameState):
        q = await self.fetch_question(state.em_portugues)
        state.active_question = q
        self.hidden_options[state.user_id] = []

        embed = self.build_embed(state)
        view = self.build_view(state)

        if isinstance(target, discord.Interaction):
            await target.response.send_message(embed=embed, view=view)
        else:
            await target.send(embed=embed, view=view)

    async def handle_answer(self, inter: discord.Interaction, state: GameState, choice: int):
        correct = choice == state.active_question.correct
        state.lose_jokers_or_levels(not correct)
        if correct:
            await inter.response.send_message("✅ Correto!", ephemeral=True)
        else:
            await inter.response.send_message("❌ Errado!", ephemeral=True)
        await self.after_answer(inter.channel, state)

    async def after_answer(self, ctx, state: GameState):
        state.current_index += 1
        if state.current_index >= len(PRIZES):
            prize = PRIZES[state.prize_level] if state.prize_level >= 0 else 0
            await ctx.send(f"🎉 Fim! Ganhou **{prize}€**")
            del self.states[state.user_id]
        else:
            await self.next_question(ctx, state)

# -------------------- Setup --------------------

async def setup(bot):
    await bot.add_cog(JokerCog(bot))
