from datetime import datetime, timezone
import secrets

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from auth import hash_agent_token, verify_api_key
from db import get_conn
from hl_client import get_market_candles


router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)


class CreateAgentRequest(BaseModel):
    user_id: str
    


class ConnectAgentRequest(BaseModel):
    connection_token: str
    agent_name: str | None = None
    provider: str | None = None


class HeartbeatRequest(BaseModel):
    agent_token: str


class DisconnectRequest(BaseModel):
    agent_token: str



def _extract_api_key(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header",
        )

    return authorization.removeprefix("Bearer ").strip()


@router.post("/create")
def create_agent(
    req: CreateAgentRequest,
    authorization: str | None = Header(None),
):
    api_key = _extract_api_key(authorization)
    with get_conn() as conn:
        conn.execute(
            """
            SELECT
                id,
                api_key_hash,
                wallet_address,
                agent_address
            FROM users
            WHERE id = %s
            """,
            (req.user_id,),
        )

        user = conn.fetchone()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        if (
            not user["api_key_hash"]
            or not verify_api_key(
                api_key,
                user["api_key_hash"],
            )
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
            )

        if not user["wallet_address"]:
            raise HTTPException(
                status_code=409,
                detail="Wallet not linked",
            )

        if not user["agent_address"]:
            raise HTTPException(
                status_code=409,
                detail="Agent wallet has not been created",
            )

        # If this user already has a live agent connection,
        # don't create another one.
        conn.execute(
            """
            SELECT
                id
            FROM agent_connections
            WHERE user_id = %s
              AND connected = 1
            ORDER BY id DESC
            LIMIT 1
            """,
            (req.user_id,),
        )

        existing = conn.fetchone()

        if existing is not None:
            return {
                "connected": True,
                "already_connected": True,
                "message": (
                    "Agent is already connected. "
                    "Use the existing agent token."
                ),
            }

        # Create a fresh ONE-TIME connection token.
        token_hash = hash_agent_token(token)
        
        token = (
            "alias_connect_"
            + secrets.token_urlsafe(32)
        )

        conn.execute(
            """
            INSERT INTO agent_connections
            (
                user_id,
                token_hash,
                agent_token_hash,
                connected,
                created_at
            )
            VALUES (%s, %s, NULL, 0, %s)
            """,
            (
                req.user_id,
                token_hash,
                datetime.now(
                    timezone.utc
                ).isoformat(),
            ),
        )

    return {
        "connection_token": token,
        "skill_url": "/skill",
        "prompt": (
            "Connect this agent to Alias.\n\n"
            "First read {base_url}/skill.\n\n"
            "Then call POST {base_url}/agent/connect "
            "with this JSON:\n\n"
            f'{{"connection_token":"{token}",'
            '"agent_name":"<your agent name>",'
            '"provider":"<your provider>"}\n\n'
            "The response contains an agent_token. "
            "Store that token securely.\n\n"
            "Use it for authenticated Alias requests as:\n"
            "Authorization: Bearer <agent_token>"
        ),
    }

@router.get("/profile/{user_id}")
def get_agent_profile(
    user_id: str,
    authorization: str | None = Header(None),
):
    api_key = _extract_api_key(authorization)

    with get_conn() as conn:

        conn.execute(
            """
            SELECT
                id,
                wallet_address,
                agent_address,
                permissions_confirmed,
                api_key_hash
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )

        user = conn.fetchone()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if (
        not user["api_key_hash"]
        or not verify_api_key(
            api_key,
            user["api_key_hash"],
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return {
        "user_id": user["id"],
        "wallet_address": user["wallet_address"],
        "agent_address": user["agent_address"],
        "wallet_connected": bool(
            user["wallet_address"]
        ),
        "agent_created": bool(
            user["agent_address"]
        ),
        "permissions_approved": bool(
            user["permissions_confirmed"]
        ),
    }


@router.post("/connect")
def connect_agent(
    req: ConnectAgentRequest,
):
    with get_conn() as conn:

        conn.execute(
            """
            SELECT
                *
            FROM agent_connections
            WHERE token_hash = %s
            """,
            (hash_agent_token(req.connection_token),),
        )

        connection = conn.fetchone()

        if connection is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid connection token",
            )

        # The connection token is intentionally one-time.
        if connection["connected"]:
            raise HTTPException(
                status_code=409,
                detail="Connection token has already been used",
            )

        conn.execute(
            """
            SELECT
                wallet_address,
                agent_address
            FROM users
            WHERE id = %s
            """,
            (connection["user_id"],),
        )

        user = conn.fetchone()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        if not user["wallet_address"]:
            raise HTTPException(
                status_code=409,
                detail="Wallet not linked",
            )

        if not user["agent_address"]:
            raise HTTPException(
                status_code=409,
                detail="Agent wallet not created",
            )

        # Generate a SEPARATE long-lived agent token.
        agent_token = (
            "alias_agent_"
            + secrets.token_urlsafe(48)
        )
        agent_token_hash = hash_agent_token(agent_token)

        now = datetime.now(
            timezone.utc
        ).isoformat()

        conn.execute(
            """
            UPDATE agent_connections
            SET
                connected = 1,
                agent_token_hash = %s,
                agent_name = %s,
                provider = %s,
                connected_at = %s
            WHERE id = %s
            """,
            (
                agent_token_hash,
                req.agent_name,
                req.provider,
                now,
                connection["id"],
            ),
        )

        conn.execute(
            """
            UPDATE users
            SET last_seen = %s
            WHERE id = %s
            """,
            (
                now,
                connection["user_id"],
            ),
        )

    return {
        "connected": True,
        "user_id": connection["user_id"],
        "agent_token": agent_token,
        "message": "Agent connected successfully.",
    }


@router.post("/heartbeat")
def heartbeat(
    req: HeartbeatRequest,
):

    with get_conn() as conn:

        conn.execute(
            """
            SELECT user_id
            FROM agent_connections
            WHERE agent_token_hash = %s
              AND connected = 1
            """,
            (hash_agent_token(req.agent_token),),
        )

        connection = conn.fetchone()

        if connection is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid agent token",
            )

        now = datetime.now(
            timezone.utc
        ).isoformat()

        conn.execute(
            """
            UPDATE users
            SET last_seen = %s
            WHERE id = %s
            """,
            (
                now,
                connection["user_id"],
            ),
        )

    return {
        "alive": True,
    }


@router.post("/disconnect")
def disconnect(
    req: DisconnectRequest,
):

    with get_conn() as conn:

        conn.execute(
            """
            SELECT user_id
            FROM agent_connections
            WHERE agent_token_hash = %s
              AND connected = 1
            """,
            (hash_agent_token(req.agent_token),),
        )

        connection = conn.fetchone()

        if connection is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid agent token",
            )

        conn.execute(
            """
            UPDATE agent_connections
            SET connected = 0
            WHERE agent_token_hash = %s
            """,
            (hash_agent_token(req.agent_token),),
        )

    return {
        "success": True,
    }


@router.get("/history/{user_id}")
def trade_history(
    user_id: str,
    authorization: str | None = Header(None),
):
    api_key = _extract_api_key(authorization)

    with get_conn() as conn:

        conn.execute(
            """
            SELECT id, api_key_hash
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )

        user = conn.fetchone()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        if (
            not user["api_key_hash"]
            or not verify_api_key(
                api_key,
                user["api_key_hash"],
            )
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
            )

        conn.execute(
            """
            SELECT
                id,
                coin,
                is_buy,
                size,
                reasoning,
                confidence,
                model,
                strategy,
                result,
                created_at
            FROM trades
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 100
            """,
            (user_id,),
        )

        trades = conn.fetchall()

    return {
        "trades": [
            dict(trade)
            for trade in trades
        ]
    }


@router.get("/markets/{coin}/candles")
def market_candles(
    coin: str,
    interval: str = "1h",
    hours: int = 48,
):
    return {
        "candles": get_market_candles(
            coin,
            interval,
            hours,
        )
    }
