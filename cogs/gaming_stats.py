import time
import discord
from discord.ext import commands
from discord import app_commands
from config import GUILD_ID


class GamingStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # user_id -> { game, started_at, guild_id }
        self.active_sessions = {}

    # -------- COMMAND --------

    @app_commands.command(
        name="gaming_stats",
        description="Mostra quanto tempo alguém jogou cada jogo"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def gaming_stats(
        self,
        interaction: discord.Interaction,
        membro: discord.Member | None = None,
    ):
        membro = membro or interaction.user

        stats = await self.bot.database.get_user_stats(
            membro.id, interaction.guild.id
        )

        if not stats:
            await interaction.response.send_message(
                "🎮 Ainda não há stats registados para este jogador."
            )
            return

        embed = discord.Embed(
            title=f"🎮 Gaming stats de {membro.display_name}",
            color=discord.Color.blurple(),
        )

        for game, duration in stats:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            embed.add_field(
                name=game,
                value=f"{hours}h {minutes}m",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(GamingStats(bot))