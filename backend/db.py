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
    id UUID PRIMARY KEY,
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
    user_id UUID NOT NULL,
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
    user_id UUID NOT NULL,
    token TEXT UNIQUE NOT NULL,
    agent_token TEXT UNIQUE,
    connected INTEGER DEFAULT 0,
    agent_name TEXT,
    provider TEXT,
    created_at TIMESTAMP,
    connected_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bridge_transfers (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
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
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider TEXT",
            "ALTER TABLE trades ADD COLUMN IF NOT EXISTS reasoning TEXT",
            "ALTER TABLE trades ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION",
            "ALTER TABLE trades ADD COLUMN IF NOT EXISTS model TEXT",
            "ALTER TABLE trades ADD COLUMN IF NOT EXISTS strategy TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_id TEXT",
            "ALTER TABLE agent_connections ADD COLUMN IF NOT EXISTS agent_token TEXT UNIQUE",
            "ALTER TABLE agent_connections ADD COLUMN IF NOT EXISTS token_hash TEXT",
            "ALTER TABLE agent_connections ALTER COLUMN token DROP NOT NULL",
            "ALTER TABLE agent_connections ADD COLUMN IF NOT EXISTS agent_token_hash TEXT",
            "ALTER TABLE bridge_transfers ADD COLUMN IF NOT EXISTS withdrawal_id TEXT",
            "ALTER TABLE bridge_transfers ADD COLUMN IF NOT EXISTS destination TEXT",
            "ALTER TABLE bridge_transfers ADD COLUMN IF NOT EXISTS relay_destination TEXT",
            "ALTER TABLE bridge_transfers ADD COLUMN IF NOT EXISTS forward_tx_hash TEXT",
            "ALTER TABLE bridge_transfers ADD COLUMN IF NOT EXISTS error TEXT",

        ]

        # Run ALL migrations before creating indexes that depend on them.
        for statement in migrations:
            conn.execute(statement)

        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_agent_connections_token_hash
            ON agent_connections(token_hash)
            WHERE token_hash IS NOT NULL
            """
        )

        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_agent_connections_agent_token_hash
            ON agent_connections(agent_token_hash)
            WHERE agent_token_hash IS NOT NULL
            """
        )

        conn.execute(
            '''
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_bridge_transfers_withdrawal_id
            ON bridge_transfers(withdrawal_id)
            WHERE withdrawal_id IS NOT NULL
            '''
        )

        from auth import hash_agent_token

        # Migrate existing plaintext connection tokens.
        conn.execute(
            """
            SELECT id, token
            FROM agent_connections
            WHERE token IS NOT NULL
              AND token_hash IS NULL
            """
        )

        connection_tokens = conn.fetchall()

        for row in connection_tokens:
            conn.execute(
                """
                UPDATE agent_connections
                SET token_hash = %s
                WHERE id = %s
                """,
                (
                    hash_agent_token(row["token"]),
                    row["id"],
                ),
            )

        # Migrate existing plaintext agent tokens.
        conn.execute(
            """
            SELECT id, agent_token
            FROM agent_connections
            WHERE agent_token IS NOT NULL
              AND agent_token_hash IS NULL
            """
        )

        agent_tokens = conn.fetchall()

        for row in agent_tokens:
            conn.execute(
                """
                UPDATE agent_connections
                SET agent_token_hash = %s
                WHERE id = %s
                """,
                (
                    hash_agent_token(row["agent_token"]),
                    row["id"],
                ),
            )
            

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
