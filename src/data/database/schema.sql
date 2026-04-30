-- ============================================================
-- KTSTOCK - Database Schema (SQLite)
-- Phiên bản: 1.0.0
-- ============================================================

-- === Bảng Users ===
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('admin', 'analyst', 'user', 'guest')),
    language TEXT DEFAULT 'vi' CHECK(language IN ('vi', 'en')),
    is_active INTEGER DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- === Bảng Sessions ===
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- === Bảng Symbols (Mã cổ phiếu & crypto) ===
CREATE TABLE IF NOT EXISTS symbols (
    symbol TEXT PRIMARY KEY,
    name TEXT,
    exchange TEXT NOT NULL, -- HOSE, HNX, UPCOM, BINANCE
    asset_type TEXT NOT NULL DEFAULT 'stock', -- stock, crypto, etf, index
    sector TEXT,
    industry TEXT,
    is_active INTEGER DEFAULT 1,
    metadata TEXT, -- JSON extra data
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- === Bảng Price History ===
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    interval TEXT DEFAULT '1D',
    source TEXT DEFAULT 'VCI',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES symbols(symbol),
    UNIQUE(symbol, date, interval)
);

-- === Bảng Financial Data ===
CREATE TABLE IF NOT EXISTS financial_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    report_type TEXT NOT NULL, -- income, balance, cashflow, ratio
    period TEXT NOT NULL,      -- Q1-2024, 2024
    data TEXT NOT NULL,        -- JSON
    source TEXT DEFAULT 'VCI',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES symbols(symbol),
    UNIQUE(symbol, report_type, period)
);

-- === Bảng Portfolios ===
CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    initial_capital REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- === Bảng Positions (Vị thế trong portfolio) ===
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 0,
    avg_price REAL NOT NULL DEFAULT 0,
    current_price REAL,
    notes TEXT,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    FOREIGN KEY (symbol) REFERENCES symbols(symbol)
);

-- === Bảng Watchlists ===
CREATE TABLE IF NOT EXISTS watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL DEFAULT 'Mặc định',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- === Bảng Watchlist Items ===
CREATE TABLE IF NOT EXISTS watchlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watchlist_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE,
    FOREIGN KEY (symbol) REFERENCES symbols(symbol),
    UNIQUE(watchlist_id, symbol)
);

-- === Bảng Alerts ===
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    condition TEXT NOT NULL,
    threshold REAL,
    notification_type TEXT DEFAULT 'in_app',
    is_active INTEGER DEFAULT 1,
    last_triggered TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (symbol) REFERENCES symbols(symbol)
);

-- === Bảng Alert History ===
CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,
    triggered_value REAL,
    message TEXT,
    is_read INTEGER DEFAULT 0,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE
);

-- === Bảng AI Analysis ===
CREATE TABLE IF NOT EXISTS ai_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    provider TEXT NOT NULL, -- gemini, grok, deepseek
    analysis_type TEXT DEFAULT 'general',
    prompt TEXT,
    analysis_text TEXT NOT NULL,
    confidence REAL,
    metadata TEXT, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES symbols(symbol)
);

-- === Bảng User Settings ===
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    theme TEXT DEFAULT 'dark',
    language TEXT DEFAULT 'vi',
    default_exchange TEXT DEFAULT 'HOSE',
    default_interval TEXT DEFAULT '1D',
    notifications_enabled INTEGER DEFAULT 1,
    settings_json TEXT, -- Extra settings as JSON
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- === Bảng Cache Metadata ===
CREATE TABLE IF NOT EXISTS cache_metadata (
    cache_key TEXT PRIMARY KEY,
    data_type TEXT NOT NULL,
    file_path TEXT,
    expires_at TIMESTAMP NOT NULL,
    size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- === Bảng App Config (System-wide) ===
CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_price_history_symbol ON price_history(symbol);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date);
CREATE INDEX IF NOT EXISTS idx_price_history_symbol_date ON price_history(symbol, date);
CREATE INDEX IF NOT EXISTS idx_financial_data_symbol ON financial_data(symbol);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_symbol ON ai_analysis(symbol);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_metadata(expires_at);

-- ============================================================
-- DEFAULT DATA
-- ============================================================
-- Admin user mặc định (password: Admin@123)
INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role)
VALUES ('admin', 'admin@ktstock.local',
        '$2b$12$2eG9uxqx3GE1fAhNhICQoeecrgCtJFYRnLPRG.tnye2Vut1TR36HC',
        'Administrator', 'admin');

-- App config mặc định
INSERT OR IGNORE INTO app_config (key, value, description)
VALUES
    ('app_version', '1.0.0', 'Phiên bản ứng dụng'),
    ('default_ai_provider', 'gemini', 'AI provider mặc định'),
    ('maintenance_mode', 'false', 'Chế độ bảo trì'),
    ('max_api_calls_per_minute', '30', 'Rate limit API');
