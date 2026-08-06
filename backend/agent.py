from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import secrets
import sqlite3
from datetime import datetime, timezone

router = APIRouter(prefix="/agent", tags=["agent"])


class CreateAgentRequest(BaseModel):
    user_id: str
    api_key: str


@router.post("/create")
def create_agent(req: CreateAgentRequest):
    token = "alias_live_" + secrets.token_urlsafe(32)

    conn = sqlite3.connect("alias.db")
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO agent_connections
        (
            user_id,
            token,
            connected,
            created_at
        )
        VALUES
        (?, ?, ?, ?)
        """,
        (
            req.user_id,
            token,
            0,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    conn.commit()
    conn.close()

    prompt = f"""
You are connecting to Alias.

Read the instructions in ALIAS.md.

Connection Token:
{token}

Authenticate by calling

POST /agent/connect

Body:

{{
    "connection_token": "{token}"
}}

After authentication you may begin trading.
""".strip()

    return {
        "connection_token": token,
        "prompt": prompt,
    }
