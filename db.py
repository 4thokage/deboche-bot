import sqlite3
from pathlib import Path
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "bot_data.sqlite"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()
        # Users table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT UNIQUE NOT NULL,
            name TEXT,
            bio TEXT,
            zone TEXT,
            position TEXT,
            is_police INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 0,
            gender TEXT,
            beers INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 0,
            joined_at TEXT,
            commands_count INTEGER DEFAULT 0
        )
        """)

        # Inventory table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            qty INTEGER DEFAULT 0,
            selling INTEGER DEFAULT 0,
            price INTEGER DEFAULT 0,
            UNIQUE(user_id, item),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
        self.conn.commit()

    # ------------------------
    # Helpers
    # ------------------------
    def ensure_user(self, discord_id: str):
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE discord_id=?", (discord_id,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users(discord_id, joined_at) VALUES (?, ?)",
                (discord_id, datetime.utcnow().isoformat()),
            )
            self.conn.commit()

    def get_user(self, discord_id: str):
        self.ensure_user(discord_id)
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE discord_id=?", (discord_id,))
        return cur.fetchone()

    def update_profile(self, discord_id: str, **fields):
        keys = ", ".join(f"{k}=?" for k in fields.keys())
        values = list(fields.values()) + [discord_id]
        self.conn.execute(f"UPDATE users SET {keys} WHERE discord_id=?", values)
        self.conn.commit()

    def get_user_id(self, discord_id: str) -> int:
        self.ensure_user(discord_id)
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM users WHERE discord_id=?", (discord_id,))
        row = cur.fetchone()
        return row["id"] if row else None


    def get_inventory(self, discord_id: str):
        """Return a list of all items (as Row) for a user."""
        user_id = self.get_user_id(discord_id)
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM inventory WHERE user_id=?", (user_id,))
        return cur.fetchall()


    def add_item(self, discord_id: str, item: str, qty: int = 1, price: int = 0, selling: bool = False):
        """Insert or increase quantity of an item."""
        user_id = self.get_user_id(discord_id)
        cur = self.conn.cursor()

        cur.execute("SELECT qty FROM inventory WHERE user_id=? AND item=?", (user_id, item))
        row = cur.fetchone()
        if row:
            new_qty = row["qty"] + qty
            cur.execute("UPDATE inventory SET qty=? WHERE user_id=? AND item=?", (new_qty, user_id, item))
        else:
            cur.execute(
                "INSERT INTO inventory(user_id, item, qty, price, selling) VALUES (?, ?, ?, ?, ?)",
                (user_id, item, qty, price, int(selling)),
            )
        self.conn.commit()


    def update_item(self, discord_id: str, item: str, **fields):
        """Update qty, price, or selling status for an item."""
        user_id = self.get_user_id(discord_id)
        keys = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [user_id, item]
        self.conn.execute(
            f"UPDATE inventory SET {keys} WHERE user_id=? AND item=?",
            values
        )
        self.conn.commit()


    def remove_item(self, discord_id: str, item: str, qty: int = 1):
        """Decrease quantity or remove completely if 0."""
        user_id = self.get_user_id(discord_id)
        cur = self.conn.cursor()
        cur.execute("SELECT qty FROM inventory WHERE user_id=? AND item=?", (user_id, item))
        row = cur.fetchone()
        if not row:
            return
        new_qty = row["qty"] - qty
        if new_qty > 0:
            cur.execute("UPDATE inventory SET qty=? WHERE user_id=? AND item=?", (new_qty, user_id, item))
        else:
            cur.execute("DELETE FROM inventory WHERE user_id=? AND item=?", (user_id, item))
        self.conn.commit()