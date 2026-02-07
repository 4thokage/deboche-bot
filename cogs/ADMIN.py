import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from config import GUILD_ID


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
        self.discord_id = discord_id
        self.modal_class = modal_class
        self.database = db

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
        await interaction.response.defer(ephemeral=True)

        new_pos = self.position_select.values[0]
        await self.database.update_profile(self.discord_id, position=new_pos)

        await interaction.followup.send(
            f"✅ Posição alterada para **{new_pos}**"
        )

    async def toggle_police(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        row = await self.database.get_user(self.discord_id)
        new_status = 0 if row["is_police"] else 1
        await self.database.update_profile(self.discord_id, is_police=new_status)

        await interaction.followup.send(
            f"✅ Polícia: {'🚓 Sim' if new_status else 'Não'}"
        )

    async def open_modal(self, interaction: discord.Interaction):
        row = await self.database.get_user(self.discord_id)
        modal = self.modal_class(self.database, self.discord_id, row)
        await interaction.response.send_modal(modal)

class ProfileEditModal(discord.ui.Modal, title="Editar Perfil"):
    """Modal para editar o resto do perfil."""

    def __init__(self, db, discord_id: str, row):
        super().__init__()
        self.database = db
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
        await self.database.update_profile(
            self.discord_id,
            name=self.name.value or None,
            bio=self.bio.value or None,
            zone=self.zone.value or None,
            gender=self.gender.value or None
        )
        await interaction.response.send_message("✅ Perfil atualizado!", ephemeral=True)

class ADMIN(commands.Cog, name="admin"):
    def __init__(self, bot) -> None:
        self.bot = bot
        # Estrutura de avisos em memória: {guild_id: {user_id: [warn_entry, ...]}}
        self.warnings_db = {}
        self.next_warn_id = 1  # ID sequencial dos avisos

    # ---------- SYNC ----------
    @app_commands.command(name="sync", description="Sincroniza todos os comandos de aplicação com o servidor.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def sync_tree(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            synced = await self.bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            await interaction.followup.send(f"✅ Sincronizados {len(synced)} comandos para este servidor.")
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao sincronizar comandos:\n`{e}`")

    @commands.hybrid_command(
        name="nick",
        description="Alterar o nickname de um utilizador no servidor.",
    )
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.describe(
        user="O utilizador que deverá ter um novo nickname.",
        nickname="O novo nickname a definir.",
    )
    @app_commands.guilds(discord.Object(GUILD_ID))
    async def nick(
        self, context: Context, user: discord.User, *, nickname: str = None
    ) -> None:
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        try:
            await member.edit(nick=nickname)
            embed = discord.Embed(
                description=f"**{member}** agora tem o nickname **{nickname}**!",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
        except:
            embed = discord.Embed(
                description="Ocorreu um erro ao tentar alterar o nickname do utilizador. Certifica-te que o meu cargo está acima do cargo do utilizador.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_group(
        name="aviso",
        description="Gerir avisos de um utilizador no servidor.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.guilds(discord.Object(GUILD_ID))
    async def aviso(self, context: Context) -> None:
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="Por favor, especifica um subcomando.\n\n**Subcomandos:**\n`adicionar` - Adicionar um aviso a um utilizador.\n`remover` - Remover um aviso a um utilizador.\n`listar` - Listar todos os avisos de um utilizador.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @aviso.command(
        name="adicionar",
        description="Adiciona um aviso a um utilizador no servidor.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="O utilizador que deverá receber um aviso.",
        reason="O motivo do aviso.",
    )
    @app_commands.guilds(discord.Object(GUILD_ID))
    async def aviso_adicionar(
        self, context: Context, user: discord.User, *, reason: str = "Não especificado"
    ) -> None:
        guild_id = context.guild.id
        user_id = user.id

        # Inicializa listas em memória se necessário
        self.warnings_db.setdefault(guild_id, {}).setdefault(user_id, [])

        # Criar aviso
        warn_entry = {
            "warn_id": self.next_warn_id,
            "author_id": context.author.id,
            "reason": reason,
            "timestamp": int(datetime.now().timestamp()),
        }
        self.warnings_db[guild_id][user_id].append(warn_entry)
        self.next_warn_id += 1
        total = len(self.warnings_db[guild_id][user_id])

        embed = discord.Embed(
            description=f"**{user}** recebeu um aviso de **{context.author}**!\nTotal de avisos deste utilizador: {total}",
            color=0xBEBEFE,
        )
        embed.add_field(name="Motivo:", value=reason)
        await context.send(embed=embed)

        try:
            await user.send(
                f"Recebeste um aviso de **{context.author}** em **{context.guild.name}**!\nMotivo: {reason}"
            )
        except:
            await context.send(
                f"{user.mention}, recebeste um aviso de **{context.author}**!\nMotivo: {reason}"
            )

    @aviso.command(
        name="remover",
        description="Remove um aviso de um utilizador no servidor.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="O utilizador que deverá ter o aviso removido.",
        warn_id="O ID do aviso que deverá ser removido.",
    )
    @app_commands.guilds(discord.Object(GUILD_ID))
    async def aviso_remover(
        self, context: Context, user: discord.User, warn_id: int
    ) -> None:
        guild_id = context.guild.id
        user_id = user.id
        user_warns = self.warnings_db.get(guild_id, {}).get(user_id, [])

        removed = False
        for warn in user_warns:
            if warn["warn_id"] == warn_id:
                user_warns.remove(warn)
                removed = True
                break

        total = len(user_warns)
        if removed:
            embed = discord.Embed(
                description=f"O aviso **#{warn_id}** de **{user}** foi removido!\nTotal de avisos deste utilizador: {total}",
                color=0xBEBEFE,
            )
        else:
            embed = discord.Embed(
                description=f"Não foi encontrado o aviso **#{warn_id}** para {user}.",
                color=0xE02B2B,
            )
        await context.send(embed=embed)

    @aviso.command(
        name="listar",
        description="Mostra os avisos de um utilizador no servidor.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @app_commands.describe(user="O utilizador do qual queres ver os avisos.")
    @app_commands.guilds(discord.Object(GUILD_ID))
    async def aviso_listar(self, context: Context, user: discord.User) -> None:
        guild_id = context.guild.id
        user_id = user.id
        warnings_list = self.warnings_db.get(guild_id, {}).get(user_id, [])

        embed = discord.Embed(title=f"Avisos de {user}", color=0xBEBEFE)
        if not warnings_list:
            embed.description = "Este utilizador não tem avisos."
        else:
            description = ""
            for warning in warnings_list:
                description += f"• Aviso dado por <@{warning['author_id']}>: **{warning['reason']}** (<t:{warning['timestamp']}>) - ID do Aviso #{warning['warn_id']}\n"
            embed.description = description
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="purge",
        description="Apaga um número de mensagens.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="O número de mensagens a apagar.")
    @app_commands.guilds(discord.Object(GUILD_ID))
    async def purge(self, context: Context, amount: int) -> None:
        await context.send("A apagar mensagens...")
        purged_messages = await context.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            description=f"**{context.author}** apagou **{len(purged_messages)-1}** mensagens!",
            color=0xBEBEFE,
        )
        await context.channel.send(embed=embed)

    @commands.hybrid_command(
        name="arquivo",
        description="Guarda num ficheiro de texto as últimas mensagens com um limite definido.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        limit="O limite de mensagens a arquivar.",
    )
    @app_commands.guilds(discord.Object(GUILD_ID))
    async def arquivo(self, context: Context, limit: int = 10) -> None:
        log_file = f"{context.channel.id}.log"
        with open(log_file, "w", encoding="UTF-8") as f:
            f.write(
                f'Mensagens arquivadas de: #{context.channel} ({context.channel.id}) no servidor "{context.guild}" ({context.guild.id}) em {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n'
            )
            async for message in context.channel.history(
                limit=limit, before=context.message
            ):
                attachments = [a.url for a in message.attachments]
                attachments_text = (
                    f"[Ficheiro{'s' if len(attachments) >= 2 else ''} anexado{'s' if len(attachments) >= 2 else ''}: {', '.join(attachments)}]"
                    if attachments
                    else ""
                )
                f.write(
                    f"{message.created_at.strftime('%d.%m.%Y %H:%M:%S')} {message.author} {message.id}: {message.clean_content} {attachments_text}\n"
                )
        f = discord.File(log_file)
        await context.send(file=f)
        os.remove(log_file)
        
    @app_commands.command(
        name="stats",
        description="Mostra estatísticas de uso dos comandos"
    )
    @app_commands.describe(
        least="Mostrar os comandos menos usados em vez dos mais usados"
    )
    @app_commands.guilds(discord.Object(GUILD_ID))
    async def stats(self, interaction: discord.Interaction, least: bool = False):
        await interaction.response.defer()
        top_commands = await self.bot.database.get_command_stats(limit=20, ascending=least)

        if not top_commands:
            return await interaction.followup.send("Nenhum comando registado ainda.")

        description = "\n".join(f"**{name}** → {count} usos" for name, count in top_commands)
        title = "Comandos menos usados" if least else "Comandos mais usados"

        embed = discord.Embed(
            title=title,
            description=description,
            color=0x00FF00
        )
        await interaction.followup.send(embed=embed)

    async def setup(bot: commands.Bot):
        await bot.add_cog(Stats(bot))
        
    @app_commands.command(name="perfil", description="Mostra ou edita o perfil de alguém")
    @app_commands.describe(editar="Mostra botões para editar o teu perfil", user="Outro utilizador")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def profile(self, interaction: discord.Interaction, editar: bool = False, user: discord.User | None = None):
        db = self.bot.database
        target = user or interaction.user
        target_id = str(target.id)

        row = await db.get_user(target_id)
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
        embed.add_field(name="Cervejas", value=row["commands_count"], inline=True)
        embed.add_field(name="Polícia?", value="🚓 Sim" if row["is_police"] else "Não", inline=True)
        embed.set_footer(text=f"Entrou em {format_joined_at(row['joined_at'])}")

        if editar and target == interaction.user:
            view = ProfileView(db, target_id, ProfileEditModal)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(ADMIN(bot))
