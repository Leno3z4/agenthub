import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    google_id TEXT UNIQUE,
    email TEXT UNIQUE,
    name TEXT,
    picture TEXT,
    x_id TEXT UNIQUE,
    wallet_address TEXT UNIQUE,
    agent_address TEXT,
    agent_key_encrypted BYTEA,
    api_key_hash TEXT,
    permissions_confirmed INTEGER DEFAULT 0,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    is_buy INTEGER NOT NULL,
    size DOUBLE PRECISION NOT NULL,
    result TEXT,
    reasoning TEXT,
    confidence DOUBLE PRECISION,
    model TEXT,
    strategy TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS agent_connections (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    connected INTEGER DEFAULT 0,
    agent_name TEXT,
    provider TEXT,
    created_at TIMESTAMP,
    connected_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bridge_transfers (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    amount_usdc DOUBLE PRECISION NOT NULL,
    burn_tx_hash TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def init_db():
    statements = [
        statement.strip()
        for statement in SCHEMA.split(";")
        if statement.strip()
    ]

    with get_conn() as conn:
        for statement in statements:
            conn.execute(statement)

        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS picture TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS x_id TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_address TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS agent_address TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS agent_key_encrypted BYTEA",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key_hash TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions_confirmed INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE trades ADD COLUMN IF NOT EXISTS reasoning TEXT",
            "ALTER TABLE trades ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION",
            "ALTER TABLE trades ADD COLUMN IF NOT EXISTS model TEXT",
            "ALTER TABLE trades ADD COLUMN IF NOT EXISTS strategy TEXT",
        ]

        for statement in migrations:
            conn.execute(statement)


@contextmanager
def get_conn():
    conn = psycopg2.connect(DATABASE_URL)

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            yield cursor

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
