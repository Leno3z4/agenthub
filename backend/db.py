import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    google_id TEXT UNIQUE,
    auth_provider TEXT,
    email TEXT UNIQUE,
    name TEXT,
    picture TEXT,

    x_id TEXT UNIQUE,

    wallet_address TEXT UNIQUE,
    agent_address TEXT,
    agent_key_encrypted BLOB,
    api_key_hash TEXT,
    permissions_confirmed INTEGER DEFAULT 0,
    last_seen TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    is_buy INTEGER NOT NULL,
    size REAL NOT NULL,
    result TEXT,
    reasoning TEXT,
    confidence REAL,
    model TEXT,
    strategy TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS bridge_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    amount_usdc REAL NOT NULL,
    burn_tx_hash TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN api_key_hash TEXT",
    "ALTER TABLE users ADD COLUMN permissions_confirmed INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN last_seen TEXT",
    "ALTER TABLE users ADD COLUMN auth_provider TEXT",
    "ALTER TABLE trades ADD COLUMN reasoning TEXT",
    "ALTER TABLE trades ADD COLUMN confidence REAL",
    "ALTER TABLE trades ADD COLUMN model TEXT",
    "ALTER TABLE trades ADD COLUMN strategy TEXT",
    "ALTER TABLE users ADD COLUMN google_id TEXT",
    "ALTER TABLE users ADD COLUMN email TEXT",
    "ALTER TABLE users ADD COLUMN name TEXT",
    "ALTER TABLE users ADD COLUMN picture TEXT",
    "ALTER TABLE users ADD COLUMN x_id TEXT",
]


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        for stmt in MIGRATIONS:
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError:
                pass


@contextmanager
def get_conn():
    if DB_PATH != ":memory:":
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
