import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
import itertools

from config import GUILD_ID


class TradeSelect(discord.ui.Select):
    """Dropdown para selecionar trades existentes."""

    def __init__(self, trades: dict[int, dict]):
        options = []
        for t in trades.values():
            participant_text = f"<@{t['participant']}>" if t['participant'] else "Ninguém"
            option = discord.SelectOption(
                label=f"ID {t['id']} — {t['type']}: {t['content'][:50]}",
                description=f"Criador: <@{t['creator_id']}> | Participante: {participant_text}",
                value=str(t['id'])
            )
            options.append(option)

        super().__init__(placeholder="Escolhe uma trade...", min_values=1, max_values=1, options=options)
        self.selected_trade = None

    async def callback(self, interaction: discord.Interaction):
        self.selected_trade = int(self.values[0])
        self.view.stop()


class TradeView(discord.ui.View):
    """View que contém o dropdown de trades."""

    def __init__(self, trades: dict[int, dict]):
        super().__init__()
        self.select = TradeSelect(trades)
        self.add_item(self.select)


class Trades(commands.Cog):
    """Sistema de trocas com datas de criação e interação via dropdowns."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_trades: dict[int, dict[int, dict]] = {}
        self._id_counter = itertools.count(1)  # IDs únicos para trades

    def _get_guild_trades(self, guild_id: int):
        return self.guild_trades.setdefault(guild_id, {})

    @app_commands.command(
        name="trocas",
        description="Gerencia trocas: oferecer, pedir, entrar, aceitar, cancelar, listar"
    )
    @app_commands.describe(
        oferecer="Texto do item que estás a oferecer",
        pedir="Texto do item que procuras",
        entrar="ID da trade para entrar",
        aceitar="ID da trade para aceitar",
        cancelar="ID da trade para cancelar",
        listar="Mostrar todas as trocas"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def trocas(
        self,
        interaction: discord.Interaction,
        oferecer: Optional[str] = None,
        pedir: Optional[str] = None,
        entrar: Optional[int] = None,
        aceitar: Optional[int] = None,
        cancelar: Optional[int] = None,
        listar: Optional[bool] = False
    ):
        guild_id = interaction.guild.id
        user_id = interaction.user.id
        trades = self._get_guild_trades(guild_id)

        # Fetch user data
        user_data = await self.bot.database.get_user(user_id)
        is_police = user_data["is_police"] if user_data else 0

        if is_police:
            return await interaction.response.send_message(
                "🚫 Utilizadores com funções policiais não podem usar o sistema de trocas.",
                ephemeral=True
            )

        # --- Criar nova trade ---
        if oferecer or pedir:
            t_type = "oferta" if oferecer else "procura"
            content = oferecer or pedir
            trade_id = next(self._id_counter)
            trades[trade_id] = {
                "id": trade_id,
                "type": t_type,
                "creator_id": user_id,
                "content": content,
                "created_at": datetime.utcnow(),
                "participant": None,
                "accepted_by_creator": False,
                "accepted_by_participant": False
            }
            return await interaction.response.send_message(
                f"✅ Trade criada! ID `{trade_id}` — {content} ({t_type})"
            )

        # --- Entrar numa trade ---
        if entrar:
            trade = trades.get(entrar)
            if not trade:
                return await interaction.response.send_message("❌ Trade não encontrada", ephemeral=True)
            if trade["creator_id"] == user_id:
                return await interaction.response.send_message("❌ Não podes entrar na tua própria trade", ephemeral=True)
            if trade["participant"]:
                return await interaction.response.send_message("❌ Esta trade já tem alguém participando", ephemeral=True)
            trade["participant"] = user_id
            return await interaction.response.send_message(f"✅ Entraste na trade `{entrar}`: {trade['content']}")

        # --- Aceitar trade ---
        if aceitar:
            trade = trades.get(aceitar)
            if not trade:
                return await interaction.response.send_message("❌ Trade não encontrada", ephemeral=True)
            if user_id not in [trade["creator_id"], trade["participant"]]:
                return await interaction.response.send_message("❌ Não podes aceitar esta trade", ephemeral=True)

            if user_id == trade["creator_id"]:
                trade["accepted_by_creator"] = True
            else:
                trade["accepted_by_participant"] = True

            if trade["accepted_by_creator"] and trade["accepted_by_participant"]:
                trades.pop(aceitar)
                creator = interaction.guild.get_member(trade["creator_id"])
                participant = interaction.guild.get_member(trade["participant"])
                content = trade["content"]
                msg = f"✅ A trade `{aceitar}` foi completada! Conteúdo: {content}"
                if creator:
                    try: await creator.send(msg)
                    except: pass
                if participant:
                    try: await participant.send(msg)
                    except: pass
                return await interaction.response.send_message(msg)
            else:
                return await interaction.response.send_message(
                    f"✅ Aceitaste a trade `{aceitar}`. Aguarda o outro participante."
                )

        # --- Cancelar trade ---
        if cancelar:
            trade = trades.get(cancelar)
            if not trade:
                return await interaction.response.send_message("❌ Trade não encontrada", ephemeral=True)
            if trade["creator_id"] != user_id:
                return await interaction.response.send_message("❌ Só podes cancelar a tua própria trade", ephemeral=True)
            trades.pop(cancelar)
            return await interaction.response.send_message(f"✅ Trade `{cancelar}` cancelada.")

        # --- Listar trades ---
        if listar or not any([oferecer, pedir, entrar, aceitar, cancelar]):
            if not trades:
                return await interaction.response.send_message("📭 Não há trades atualmente.")

            # UX Krypton style: dropdown para escolher trade
            view = TradeView(trades)
            await interaction.response.send_message("Escolhe uma trade para ver detalhes:", view=view)
            await view.wait()

            if not view.select.selected_trade:
                return await interaction.followup.send("❌ Nenhuma trade selecionada.")

            trade_id = view.select.selected_trade
            t = trades[trade_id]
            participant_text = f"<@{t['participant']}>" if t['participant'] else "Ninguém"

            embed = discord.Embed(
                title=f"Trade ID {t['id']} — {t['type']}",
                description=f"📝 Conteúdo: {t['content']}\n👤 Criador: <@{t['creator_id']}>\n🤝 Participante: {participant_text}\n🕒 Criada: {t['created_at'].strftime('%d/%m/%Y %H:%M UTC')}",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Trades(bot))
