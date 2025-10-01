import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
import itertools

from config import GUILD_ID

class Trades(commands.Cog):
    """Sistema de trocas com datas de criação das entradas"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # guild_id -> dict[id -> trade]
        self.guild_trades: dict[int, dict[int, dict]] = {}
        self._id_counter = itertools.count(1)  # unique trade IDs

    def _get_guild_trades(self, guild_id: int):
        return self.guild_trades.setdefault(guild_id, {})

    @app_commands.command(
        name="trocas",
        description="Gerencia trocas: oferecer, pedir, entrar, aceitar, cancelar, listar"
    )
    @app_commands.describe(
        oferecer="Texto do item que estás a oferecer",
        pedir="Texto do item que procuras",
        entrar="ID da troca para entrar",
        aceitar="ID da troca para aceitar",
        cancelar="ID da troca para cancelar",
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

        timestamp = datetime.utcnow()
        user_data = self.bot.db.get_user(user_id)

        # BLOCK POLICE USERS
        if user_data["is_police"] == 1:
            return await interaction.response.send_message(
                "🚫 Utilizadores com funções policiais não podem usar o sistema de trocas.",
                ephemeral=True
            )

        # --- Create new trade ---
        if oferecer or pedir:
            t_type = "oferta" if oferecer else "procura"
            content = oferecer or pedir
            trade_id = next(self._id_counter)
            trades[trade_id] = {
                "id": trade_id,
                "type": t_type,
                "creator_id": user_id,
                "content": content,
                "created_at": timestamp,
                "participant": None,
                "accepted_by_creator": False,
                "accepted_by_participant": False
            }
            await interaction.response.send_message(
                f"✅ Trade criado! ID `{trade_id}` — {content} ({t_type})"
            )
            return

        # --- Join trade ---
        if entrar:
            trade = trades.get(entrar)
            if not trade:
                return await interaction.response.send_message("❌ Trade não encontrada", ephemeral=True)
            if trade["creator_id"] == user_id:
                return await interaction.response.send_message("❌ Não podes entrar na tua própria trade", ephemeral=True)
            if trade["participant"]:
                return await interaction.response.send_message("❌ Esta trade já tem alguém participando", ephemeral=True)
            trade["participant"] = user_id
            await interaction.response.send_message(f"✅ Entraste na trade `{entrar}`: {trade['content']}")
            return

        # --- Accept trade ---
        if aceitar:
            trade = trades.get(aceitar)
            if not trade:
                return await interaction.response.send_message("❌ Trade não encontrada", ephemeral=True)
            if user_id != trade["creator_id"] and user_id != trade["participant"]:
                return await interaction.response.send_message("❌ Não podes aceitar esta trade", ephemeral=True)
            
            # Marca aceitação
            if user_id == trade["creator_id"]:
                trade["accepted_by_creator"] = True
            else:
                trade["accepted_by_participant"] = True
            
            # Se ambos aceitaram
            if trade["accepted_by_creator"] and trade["accepted_by_participant"]:
                trades.pop(aceitar)
                
                # Notificar ambos os users
                creator = interaction.guild.get_member(trade["creator_id"])
                participant = interaction.guild.get_member(trade["participant"])
                content = trade["content"]
                msg = f"✅ A trade `{aceitar}` foi completada com sucesso! Conteúdo: {content}"
                
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
        
        # --- Cancel trade ---
        if cancelar:
            trade = trades.get(cancelar)
            if not trade:
                return await interaction.response.send_message("❌ Trade não encontrada", ephemeral=True)
            if trade["creator_id"] != user_id:
                return await interaction.response.send_message("❌ Só podes cancelar a tua própria trade", ephemeral=True)
            trades.pop(cancelar)
            return await interaction.response.send_message(f"✅ Trade `{cancelar}` cancelada com sucesso.")

        # --- List trades ---
        if listar or not any([oferecer, pedir, entrar, aceitar, cancelar]):
            # Filter out trades that user is not allowed to see
            visible_trades = trades
            if not visible_trades:
                return await interaction.response.send_message("📭 Não há trades atualmente.")
            
            embed = discord.Embed(title="📜 Trocas atuais", color=discord.Color.blue())
            for t in visible_trades.values():
                dt = t["created_at"].strftime("%d/%m/%Y %H:%M UTC")
                participants = f"<@{t['participant']}>" if t["participant"] else "Ninguém"
                embed.add_field(
                    name=f"ID {t['id']} — {t['type']}",
                    value=f"📝 Conteúdo: {t['content']}\n👤 Criador: <@{t['creator_id']}>\n🤝 Participante: {participants}\n🕒 Criada: {dt}",
                    inline=False
                )
            await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Trades(bot))
