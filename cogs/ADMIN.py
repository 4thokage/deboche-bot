import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from config import GUILD_ID


class Moderation(commands.Cog, name="moderação"):
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


async def setup(bot) -> None:
    await bot.add_cog(Moderation(bot))
