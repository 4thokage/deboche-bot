import aiosqlite
import datetime
from typing import Optional, Dict


class DatabaseManager:
    def __init__(self, *, connection: aiosqlite.Connection) -> None:
        self.connection = connection
        
        
        
    # ===============================
    # USERS & PROFILE
    # ===============================
    async def get_user(self, discord_id: int) -> Optional[Dict]:
        query = """
        SELECT
            u.id,
            u.discord_id,
            u.name,
            u.bio,
            u.zone,
            u.position,
            u.xp,
            u.is_police,
            u.reputation,
            u.gender,
            u.coins,
            u.joined_at,
            u.commands_count,
            s.language,
            s.notifications_enabled,
            s.sound_enabled,
            s.dark_mode,
            s.auto_reply_enabled,
            s.daily_reminder_enabled,
            s.trade_alerts_enabled
        FROM users u
        LEFT JOIN user_settings s ON s.user_id = u.id
        WHERE u.discord_id = ?
        """
        async with self.connection.execute(query, (str(discord_id),)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            keys = [
                "id", "discord_id", "name", "bio", "zone", "position",
                "xp", "is_police", "reputation", "gender",
                "coins", "joined_at", "commands_count",
                "language", "notifications_enabled", "sound_enabled", "dark_mode",
                "auto_reply_enabled", "daily_reminder_enabled", "trade_alerts_enabled"
            ]
            return dict(zip(keys, row))

    async def create_user(self, discord_id: int, name: str):
        joined_at = datetime.datetime.utcnow().isoformat()
        await self.connection.execute(
            "INSERT OR IGNORE INTO users(discord_id, name, joined_at) VALUES (?, ?, ?)",
            (str(discord_id), name, joined_at)
        )
        await self.connection.commit()
        # Create default settings
        user = await self.connection.execute("SELECT id FROM users WHERE discord_id=?", (str(discord_id),))
        async with user as cursor:
            row = await cursor.fetchone()
            if row:
                user_id = row[0]
                await self.connection.execute(
                    "INSERT OR IGNORE INTO user_settings(user_id) VALUES(?)",
                    (user_id,)
                )
                await self.connection.commit()
        return await self.get_user(discord_id)

    async def update_profile(self, discord_id: str, **kwargs):
        # First, find the user ID in the table
        user = await self.connection.execute(
            "SELECT id FROM users WHERE discord_id=?", (discord_id,)
        )
        async with user as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            user_id = row[0]

        # Only allow these fields to be updated
        allowed_fields = ["name", "bio", "zone", "gender", "position", "is_police"]
        fields = []
        values = []

        for k, v in kwargs.items():
            if k in allowed_fields:
                fields.append(f"{k}=?")
                values.append(v)

        if not fields:
            return False  # nothing to update

        query = f"UPDATE users SET {', '.join(fields)} WHERE id=?"
        values.append(user_id)

        await self.connection.execute(query, tuple(values))
        await self.connection.commit()
        return True

    # ===============================
    # LEVELING & ECONOMY
    # ===============================

    async def add_xp_coins(self, discord_id: int, xp: int = 0, coins: int = 0):
        user = await self.connection.execute("SELECT id, coins FROM users WHERE discord_id=?", (str(discord_id),))
        async with user as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            user_id = row[0]
            current_coins = row[1] or 0

        # Update coins
        await self.connection.execute(
            "UPDATE users SET coins = ? WHERE id=?",
            (current_coins + coins, user_id)
        )
        # For leveling, store XP in a virtual field: commands_count used as XP proxy or extend schema if needed
        await self.connection.execute(
            "UPDATE users SET commands_count = commands_count + ? WHERE id=?",
            (xp, user_id)
        )
        await self.connection.commit()
        return True
      
    async def increment_commands_count(self, discord_id: int) -> None:
        """Increase commands_count by 1 for a user"""
        query = """
        UPDATE users
        SET commands_count = commands_count + 1
        WHERE discord_id = ?
        """
        async with self.connection.execute(query, (str(discord_id),)):
            await self.connection.commit()

    async def get_level(self, discord_id: int) -> int:
        user = await self.connection.execute("SELECT commands_count FROM users WHERE discord_id=?", (str(discord_id),))
        async with user as cursor:
            row = await cursor.fetchone()
            xp = row[0] if row else 0
        level = int((xp / 10) ** 0.5)
        return level

    async def increment_command_usage(self, discord_id: int, command_name: str) -> None:
        """Incrementa contador de uso do comando por user."""
        query = """
        INSERT INTO command_usage (discord_id, command_name, usage_count)
        VALUES (?, ?, 1)
        ON CONFLICT(discord_id, command_name)
        DO UPDATE SET usage_count = usage_count + 1
        """
        async with self.connection.execute(query, (str(discord_id), command_name)):
            await self.connection.commit()
            
    async def get_command_stats(self, limit: int = 20, ascending: bool = False):
        """
        Retorna estatísticas de todos os comandos, agregados por comando.
        :param limit: top N comandos
        :param ascending: True = menos usados primeiro
        """
        order = "ASC" if ascending else "DESC"
        query = f"""
        SELECT command_name, SUM(usage_count) as total
        FROM command_usage
        GROUP BY command_name
        ORDER BY total {order}
        LIMIT ?
        """
        rows = await self.connection.execute(query, (limit,))
        async with rows as cursor:
            return await cursor.fetchall()  # [(command_name, total), ...]
    # ===============================
    # QUESTS
    # ===============================

    async def complete_quest(self, discord_id: int, coins: int, xp: int):
        return await self.add_xp_coins(discord_id, xp=xp, coins=coins)

    # ===============================
    # PvP BATTLES
    # ===============================

    async def pvp_battle(self, user1_id: int, user2_id: int) -> Dict:
        # Get players coins + xp
        rows = await self.connection.execute(
            "SELECT discord_id, commands_count, coins FROM users WHERE discord_id IN (?, ?)",
            (str(user1_id), str(user2_id))
        )
        async with rows as cursor:
            players = await cursor.fetchall()
            if len(players) < 2:
                return {"error": "Um ou ambos os jogadores não encontrados"}

        # Battle logic
        stats = {p[0]: {"xp": p[1], "coins": p[2]} for p in players}
        attack1 = stats[str(user1_id)]["xp"] // 2 + random.randint(1, 10)
        attack2 = stats[str(user2_id)]["xp"] // 2 + random.randint(1, 10)

        if attack1 > attack2:
            winner, loser = str(user1_id), str(user2_id)
        elif attack2 > attack1:
            winner, loser = str(user2_id), str(user1_id)
        else:
            winner = loser = None  # draw

        reward_coins = random.randint(5, 25)
        reward_xp = random.randint(5, 20)

        if winner:
            await self.add_xp_coins(int(winner), xp=reward_xp, coins=reward_coins)

        return {
            "winner": winner,
            "loser": loser,
            "reward_coins": reward_coins,
            "reward_xp": reward_xp,
            "attack1": attack1,
            "attack2": attack2
        }

    async def add_warn(
        self, user_id: int, server_id: int, moderator_id: int, reason: str
    ) -> int:
        """
        This function will add a warn to the database.

        :param user_id: The ID of the user that should be warned.
        :param reason: The reason why the user should be warned.
        """
        rows = await self.connection.execute(
            "SELECT id FROM warns WHERE user_id=? AND server_id=? ORDER BY id DESC LIMIT 1",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            warn_id = result[0] + 1 if result is not None else 1
            await self.connection.execute(
                "INSERT INTO warns(id, user_id, server_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)",
                (
                    warn_id,
                    user_id,
                    server_id,
                    moderator_id,
                    reason,
                ),
            )
            await self.connection.commit()
            return warn_id

    async def remove_warn(self, warn_id: int, user_id: int, server_id: int) -> int:
        """
        This function will remove a warn from the database.

        :param warn_id: The ID of the warn.
        :param user_id: The ID of the user that was warned.
        :param server_id: The ID of the server where the user has been warned
        """
        await self.connection.execute(
            "DELETE FROM warns WHERE id=? AND user_id=? AND server_id=?",
            (
                warn_id,
                user_id,
                server_id,
            ),
        )
        await self.connection.commit()
        rows = await self.connection.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

    async def get_warnings(self, user_id: int, server_id: int) -> list:
        """
        This function will get all the warnings of a user.

        :param user_id: The ID of the user that should be checked.
        :param server_id: The ID of the server that should be checked.
        :return: A list of all the warnings of the user.
        """
        rows = await self.connection.execute(
            "SELECT user_id, server_id, moderator_id, reason, strftime('%s', created_at), id FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list
          
    # ---------- GAMING STATS ----------
    async def add_gaming_session(
        self,
        user_id: int,
        server_id: int,
        game_name: str,
        started_at: int,
        ended_at: int,
    ):
        duration = max(0, ended_at - started_at)

        await self.connection.execute(
            """
            INSERT INTO gaming_sessions
            (user_id, server_id, game_name, started_at, ended_at, duration)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, server_id, game_name, started_at, ended_at, duration),
        )

        await self.connection.execute(
            """
            INSERT INTO gaming_totals (user_id, server_id, game_name, total_duration)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, server_id, game_name)
            DO UPDATE SET total_duration = total_duration + excluded.total_duration
            """,
            (user_id, server_id, game_name, duration),
        )

        await self.connection.commit()

    async def get_user_stats(self, user_id: int, server_id: int):
        rows = await self.connection.execute(
            """
            SELECT game_name, total_duration
            FROM gaming_totals
            WHERE user_id=? AND server_id=?
            ORDER BY total_duration DESC
            """,
            (user_id, server_id),
        )

        async with rows as cursor:
            return await cursor.fetchall()