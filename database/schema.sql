CREATE TABLE IF NOT EXISTS `warns` (
  `id` int(11) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `server_id` varchar(20) NOT NULL,
  `moderator_id` varchar(20) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- TABELA DE UTILIZADORES
-- ================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT UNIQUE NOT NULL,
    name TEXT,
    bio TEXT,
    zone TEXT,
    position TEXT,
    xp INTEGER DEFAULT 0,
    is_police INTEGER DEFAULT 0,
    reputation INTEGER DEFAULT 0,
    gender TEXT,
    coins INTEGER DEFAULT 0,
    joined_at TEXT,
    commands_count INTEGER DEFAULT 0
);

-- ================================
-- TABELA DE SETTINGS DO UTILIZADOR
-- ================================
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    language TEXT DEFAULT 'pt-PT',
    notifications_enabled INTEGER DEFAULT 1,
    sound_enabled INTEGER DEFAULT 1,
    dark_mode INTEGER DEFAULT 0,
    auto_reply_enabled INTEGER DEFAULT 0,
    daily_reminder_enabled INTEGER DEFAULT 0,
    trade_alerts_enabled INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ================================
-- TABELA DE INVENTÁRIO
-- ================================
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    item_type TEXT, -- ex: consumível, skin, equipamento
    quantity INTEGER DEFAULT 1,
    rarity TEXT DEFAULT 'comum', -- comum, raro, épico, lendário
    acquired_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ================================
-- TABELA DE TROCAS / TRADES
-- ================================
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    coins_offered INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pendente', -- pendente, aceite, rejeitado
    created_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES inventory(id) ON DELETE CASCADE
);

-- ================================
-- TABELA DE LOGS DE TRADES (OPCIONAL)
-- ================================
CREATE TABLE IF NOT EXISTS trade_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL,
    action TEXT, -- criado, aceite, rejeitado
    performed_by INTEGER, -- id do user que executou a ação
    timestamp TEXT,
    FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- -------- GAMING SESSIONS (histórico) --------
CREATE TABLE IF NOT EXISTS gaming_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    server_id INTEGER NOT NULL,
    game_name TEXT NOT NULL,
    started_at INTEGER NOT NULL,
    ended_at INTEGER NOT NULL,
    duration INTEGER NOT NULL
);

-- -------- GAMING TOTALS (acumulado) --------
CREATE TABLE IF NOT EXISTS gaming_totals (
    user_id INTEGER NOT NULL,
    server_id INTEGER NOT NULL,
    game_name TEXT NOT NULL,
    total_duration INTEGER NOT NULL,
    PRIMARY KEY (user_id, server_id, game_name)
);

-- Tabela de uso de comandos
CREATE TABLE IF NOT EXISTS command_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT NOT NULL,       -- ID do user
    command_name TEXT NOT NULL,     -- nome do comando
    usage_count INTEGER DEFAULT 0,  -- vezes usadas
    UNIQUE(discord_id, command_name)
);