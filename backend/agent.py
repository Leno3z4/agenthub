from datetime import datetime, timezone
import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auth import verify_api_key
from db import get_conn

router = APIRouter(prefix="/agent", tags=["agent"])


class CreateAgentRequest(BaseModel):
    user_id: str
    api_key: str


class ConnectAgentRequest(BaseModel):
    connection_token: str
    agent_name: str | None = None
    provider: str | None = None


class HeartbeatRequest(BaseModel):
    agent_token: str


class DisconnectRequest(BaseModel):
    agent_token: str


@router.post("/create")
def create_agent(req: CreateAgentRequest):
    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, api_key_hash FROM users WHERE id = %s",
            (req.user_id,),
        ).fetchone()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if not user["api_key_hash"] or not verify_api_key(
            req.api_key,
            user["api_key_hash"],
        ):
            raise HTTPException(status_code=401, detail="Invalid API key")

        conn.execute(
            "DELETE FROM agent_connections WHERE user_id = %s AND connected = 0",
            (req.user_id,),
        )

        token = "alias_connect_" + secrets.token_urlsafe(32)

        conn.execute(
            """
            INSERT INTO agent_connections
            (user_id, token, connected, created_at)
            VALUES (%s, %s, 0, %s)
            """,
            (
                req.user_id,
                token,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    return {
        "connection_token": token,
        "skill_url": "/skill",
        "prompt": (
            "Connect this agent to Alias.\n\n"
            "First read {base_url}/skill.\n\n"
            "Then call POST {base_url}/agent/connect with this JSON:\n\n"
            f'{{"connection_token":"{token}",'
            '"agent_name":"<your agent name>",'
            '"provider":"<your provider>"}\n\n'
            "The response contains an agent_token. Store that token securely.\n\n"
            "Use it for authenticated Alias requests as:\n"
            "Authorization: Bearer <agent_token>"
        ),
    }

@router.get("/profile/{user_id}")
def get_agent_profile(
    user_id: str,
    api_key: str,
):
    """
    Restore the persistent Alias account state for a returning user.
    Only public account identifiers and setup state are returned.
    """
    with get_conn() as conn:
        user = conn.execute(
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
        ).fetchone()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if not user["api_key_hash"] or not verify_api_key(
        api_key,
        user["api_key_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return {
        "user_id": user["id"],
        "wallet_address": user["wallet_address"],
        "agent_address": user["agent_address"],
        "wallet_connected": bool(user["wallet_address"]),
        "agent_created": bool(user["agent_address"]),
        "permissions_approved": bool(
            user["permissions_confirmed"]
        ),
    }               
@router.post("/connect")
def connect_agent(req: ConnectAgentRequest):
    with get_conn() as conn:
        connection = conn.execute(
            "SELECT * FROM agent_connections WHERE token = %s",
            (req.connection_token,),
        ).fetchone()

        if connection is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid connection token",
            )

        if connection["connected"]:
            raise HTTPException(
                status_code=409,
                detail="Connection token has already been used",
            )

        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """
            UPDATE agent_connections
            SET connected = 1, agent_name = %s, provider = %s, connected_at = %s
            WHERE id = %s
            """,
            (
                req.agent_name,
                req.provider,
                now,
                connection["id"],
            ),
        )

        conn.execute(
            "UPDATE users SET last_seen = %s WHERE id = %s",
            (now, connection["user_id"]),
        )

    return {
        "connected": True,
        "user_id": connection["user_id"],
        "agent_token": req.connection_token,
        "message": "Agent connected successfully.",
    }


@router.post("/heartbeat")
def heartbeat(req: HeartbeatRequest):
    with get_conn() as conn:
        connection = conn.execute(
            """
            SELECT user_id
            FROM agent_connections
            WHERE token = %s AND connected = 1
            """,
            (req.agent_token,),
        ).fetchone()

        if connection is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid agent token",
            )

        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            "UPDATE users SET last_seen = %s WHERE id = %s",
            (now, connection["user_id"]),
        )

    return {"alive": True}


@router.post("/disconnect")
def disconnect(req: DisconnectRequest):
    with get_conn() as conn:
        connection = conn.execute(
            """
            SELECT user_id
            FROM agent_connections
            WHERE token = %s AND connected = 1
            """,
            (req.agent_token,),
        ).fetchone()

        if connection is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid agent token",
            )

        conn.execute(
            "UPDATE agent_connections SET connected = 0 WHERE token = %s",
            (req.agent_token,),
        )

    return {"success": True}
