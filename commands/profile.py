import discord
from discord import app_commands
from discord.ext import commands
from config import GUILD_ID
from datetime import datetime

def format_joined_at(value: str | None) -> str:
    if not value:
        return "??"
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return value

def get_color_by_position(position: str) -> discord.Color:
    position = (position or "").lower()
    if position == "consumidor":
        return discord.Color.blue()
    elif position == "vendedor":
        return discord.Color.green()
    elif position == "fornecedor":
        return discord.Color.orange()
    return discord.Color.dark_grey()

class ProfileView(discord.ui.View):
    """View com botões e dropdown para editar rapidamente o perfil."""

    def __init__(self, db, discord_id: str, modal_class):
        super().__init__(timeout=None)
        self.db = db
        self.discord_id = discord_id
        self.modal_class = modal_class

        # Select menu para posição
        options = [
            discord.SelectOption(label="Consumidor", value="Consumidor"),
            discord.SelectOption(label="Vendedor", value="Vendedor"),
            discord.SelectOption(label="Fornecedor", value="Fornecedor"),
        ]
        self.position_select = discord.ui.Select(
            placeholder="Alterar posição",
            options=options
        )
        self.position_select.callback = self.change_position
        self.add_item(self.position_select)

        # Botão para alternar polícia
        self.toggle_police_btn = discord.ui.Button(
            label="Alternar Polícia", style=discord.ButtonStyle.secondary
        )
        self.toggle_police_btn.callback = self.toggle_police
        self.add_item(self.toggle_police_btn)

        # Botão para abrir modal completo
        self.edit_modal_btn = discord.ui.Button(
            label="Editar perfil completo", style=discord.ButtonStyle.primary
        )
        self.edit_modal_btn.callback = self.open_modal
        self.add_item(self.edit_modal_btn)

    async def change_position(self, interaction: discord.Interaction):
        new_pos = self.position_select.values[0]
        self.db.update_profile(self.discord_id, position=new_pos)
        await interaction.response.send_message(
            f"✅ Posição alterada para **{new_pos}**", ephemeral=True
        )

    async def toggle_police(self, interaction: discord.Interaction):
        row = self.db.get_user(self.discord_id)
        new_status = 0 if row["is_police"] else 1
        self.db.update_profile(self.discord_id, is_police=new_status)
        status_text = "🚓 Sim" if new_status else "Não"
        await interaction.response.send_message(
            f"✅ Polícia: {status_text}", ephemeral=True
        )

    async def open_modal(self, interaction: discord.Interaction):
        row = self.db.get_user(self.discord_id)
        modal = self.modal_class(self.db, self.discord_id, row)
        await interaction.response.send_modal(modal)

class ProfileEditModal(discord.ui.Modal, title="Editar Perfil"):
    """Modal para editar o resto do perfil."""

    def __init__(self, db, discord_id: str, row):
        super().__init__()
        self.db = db
        self.discord_id = discord_id

        self.name = discord.ui.TextInput(label="Nome", default=row["name"] or "", required=False)
        self.bio = discord.ui.TextInput(label="Bio", style=discord.TextStyle.paragraph, default=row["bio"] or "", required=False)
        self.zone = discord.ui.TextInput(label="Zona", default=row["zone"] or "", required=False)
        self.gender = discord.ui.TextInput(label="Género", default=row["gender"] or "", required=False)

        self.add_item(self.name)
        self.add_item(self.bio)
        self.add_item(self.zone)
        self.add_item(self.gender)

    async def on_submit(self, interaction: discord.Interaction):
        self.db.update_profile(
            self.discord_id,
            name=self.name.value or None,
            bio=self.bio.value or None,
            zone=self.zone.value or None,
            gender=self.gender.value or None
        )
        await interaction.response.send_message("✅ Perfil atualizado!", ephemeral=True)

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="perfil", description="Mostra ou edita o perfil de alguém")
    @app_commands.describe(editar="Mostra botões para editar o teu perfil", user="Outro utilizador")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def profile(self, interaction: discord.Interaction, editar: bool = False, user: discord.User | None = None):
        db = self.bot.db
        target = user or interaction.user
        target_id = str(target.id)

        row = db.get_user(target_id)
        position = row["position"] or "Desconhecida"
        color = get_color_by_position(position)
        embed = discord.Embed(
            title=f"{row['name'] or target.display_name} — {row['zone'] or 'Desconhecida'}",
            description=(
                f"**Bio:** {row['bio'] or 'Ainda não escreveste nada…'}\n"
                f"**Sexo:** {row['gender'] or 'Não sei'}"
            ),
            color=color
        )
        embed.set_author(name=f"Perfil de {target.display_name}", icon_url=target.display_avatar.url)
        embed.add_field(name="Posição", value=position, inline=True)
        embed.add_field(name="Reputação", value=row["reputation"], inline=True)
        embed.add_field(name="Comandos usados", value=row["commands_count"], inline=True)
        embed.add_field(name="Polícia?", value="🚓 Sim" if row["is_police"] else "Não", inline=True)
        embed.set_footer(text=f"Entrou em {format_joined_at(row['joined_at'])}")

        if editar and target == interaction.user:
            view = ProfileView(db, target_id, ProfileEditModal)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Profile(bot))
