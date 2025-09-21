from discord.ext import commands
import discord

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.Command):
        """Fires whenever a slash command successfully runs."""
        user_id = str(interaction.user.id)
        row = self.bot.db.get_user(user_id)
        current = row["commands_count"] or 0
        self.bot.db.update_profile(user_id, commands_count=current + 1)
        
async def setup(bot):
    await bot.add_cog(Stats(bot))