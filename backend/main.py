from typing import Optional
from pathlib import Path
from rate_limit import rate_limit
from config import require
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Header,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from eth_account import Account

from db import init_db, get_conn
from crypto_utils import encrypt, decrypt
from auth import (
    generate_api_key,
    verify_api_key,
    require_internal_auth,
    hash_agent_token,
)
from agent import router as agent_router


from hl_client import (
    generate_agent_wallet,
    get_account_state,
    execute_trade,
    execute_close,
    get_markets,
    is_agent_authorized,
)

from bridge import (
    deposit_parameters,
    bridge_status,
)

from withdrawal import (
    create_withdrawal,
    process_withdrawal,
    withdrawal_status,
)


from config import (
    HYPERLIQUID_CCTP_DOMAIN,
    ARC_CCTP_DOMAIN,
)

from agent_session import (
    create_session,
    validate_session,
    touch_session,
    destroy_session,
)
MAX_TRADE_NOTIONAL = 500.0
app = FastAPI(title="Alias Backend")
app.include_router(agent_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agenthub-wine.vercel.app",
        "http://localhost:3000",
    ],
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)


@app.on_event("startup")
def startup():
    init_db()


SKILL_TEXT = Path(__file__).parent.joinpath("ALIAS_SKILL.md").read_text()


@app.get("/skill", response_class=PlainTextResponse)
def skill(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return SKILL_TEXT.replace("{base_url}", base_url)


@app.get("/", response_class=PlainTextResponse)
def root():
    return (
        "Alias backend is live. "
        "Paste /skill into your agent's chat to get started."
    )
# ---------------------------------------------------------------------
# Wallet linking
# ---------------------------------------------------------------------

class LinkWalletRequest(BaseModel):
    user_id: str
    google_id: str
    email: str
    name: str
    wallet_address: str
    picture: str | None = None

   


class LinkWalletResponse(BaseModel):
    agent_address: str
    api_key: str


@app.post("/wallet/link", response_model=LinkWalletResponse)
def link_wallet(
    request: Request,
    req: LinkWalletRequest,
    x_internal_auth: Optional[str] = Header(None),
):
    require_internal_auth(x_internal_auth)
    rate_limit(
        request,
        limit=5,
        window=60,
        identity=req.google_id,
    )

    with get_conn() as conn:
        conn.execute(
            """
            SELECT
                id,
                wallet_address,
                agent_address,
                agent_key_encrypted
            FROM users
            WHERE google_id = %s OR email = %s
            """,
            (req.google_id, req.email),
        )
        existing = conn.fetchone()
        
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="User must register first.",
            )

        if (
            existing["wallet_address"] is not None
            and existing["wallet_address"] != req.wallet_address
        ):
            raise HTTPException(
                status_code=409,
                detail="This Google account already has a different wallet linked.",
            )

        api_key, api_key_hash = generate_api_key()

        # Check whether the existing delegated agent is actually usable.
        agent_is_valid = False

        if (
            existing["agent_address"]
            and existing["agent_key_encrypted"]
        ):
            try:
                private_key = decrypt(
                    existing["agent_key_encrypted"]
                )
        
                derived_address = Account.from_key(
                    private_key
                ).address
        
                agent_is_valid = (
                    derived_address.lower()
                    == existing["agent_address"].lower()
                )
        
                if not agent_is_valid:
                    print(
                        "AGENT KEY/ADDRESS MISMATCH:",
                        existing["agent_address"],
                        derived_address,
                    )
        
            except Exception as exc:
                print(
                    "AGENT KEY VALIDATION FAILED:",
                    repr(exc),
                )
                agent_is_valid = False

        # Existing agent is healthy — keep it.
        if agent_is_valid:
            conn.execute(
                """
                UPDATE users
                SET
                    wallet_address = %s,
                    google_id = %s,
                    email = %s,
                    name = %s,
                    picture = %s,
                    api_key_hash = %s
                WHERE id = %s
                """,
                (
                    req.wallet_address,
                    req.google_id,
                    req.email,
                    req.name,
                    req.picture,
                    api_key_hash,
                    existing["id"],
                ),
            )
            conn.execute(
                """
                UPDATE agent_connections
                SET
                    connected = 0,
                    token_hash = NULL,
                    agent_token_hash = NULL
                WHERE user_id = %s
                """,
                (existing["id"],),
            )
            return LinkWalletResponse(
                agent_address=existing["agent_address"],
                api_key=api_key,
            )

        # Existing agent is corrupted/incomplete.
        # Generate a completely new delegated wallet.
        agent_address, agent_private_key = generate_agent_wallet()
        
        conn.execute(
            """
            UPDATE users
            SET
                wallet_address = %s,
                google_id = %s,
                email = %s,
                name = %s,
                picture = %s,
                agent_address = %s,
                agent_key_encrypted = %s,
                api_key_hash = %s,
                permissions_confirmed = 0
            WHERE id = %s
            """,
            (
                req.wallet_address,
                req.google_id,
                req.email,
                req.name,
                req.picture,
                agent_address,
                encrypt(agent_private_key),
                api_key_hash,
                existing["id"],
            ),
        )

        return LinkWalletResponse(
            agent_address=agent_address,
            api_key=api_key,
        )

class ConfirmPermissionsRequest(BaseModel):
    user_id: str

import uuid

class RegisterUserRequest(BaseModel):
    google_id: str | None = None
    x_id: str | None = None
    email: str | None = None
    name: str
    picture: str | None = None
    provider: str


@app.post("/agent/repair")
def repair_agent(
    request: Request,
    user_id: str,
    authorization: Optional[str] = Header(None),
):
    rate_limit(
        request,
        limit=3,
        window=60,
        identity=user_id,
    )
    user = _require_agent_auth(
        user_id,
        authorization,
    )

    agent_is_valid = False

    if (
        user["agent_address"]
        and user["agent_key_encrypted"]
    ):
        try:
            private_key = decrypt(
                user["agent_key_encrypted"]
            )

            derived_address = Account.from_key(
                private_key
            ).address

            agent_is_valid = (
                derived_address.lower()
                == user["agent_address"].lower()
            )

            if not agent_is_valid:
                print(
                    "AGENT KEY/ADDRESS MISMATCH:",
                    user["agent_address"],
                    derived_address,
                )

        except Exception as exc:
            print(
                "AGENT KEY VALIDATION FAILED:",
                repr(exc),
            )
            agent_is_valid = False

    if agent_is_valid:
        return {
            "repaired": False,
            "agent_address": user["agent_address"],
        }

    agent_address, agent_private_key = generate_agent_wallet()

    encrypted_key = encrypt(agent_private_key)

    if decrypt(encrypted_key) != agent_private_key:
        raise HTTPException(
            status_code=500,
            detail="Failed to validate newly generated agent signing key.",
        )

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE users
            SET
                agent_address = %s,
                agent_key_encrypted = %s,
                permissions_confirmed = 0
            WHERE id = %s
            """,
            (
                agent_address,
                encrypted_key,
                user_id,
            ),
        )
    
        conn.execute(
            """
            UPDATE agent_connections
            SET
                connected = 0,
                token_hash = NULL,
                agent_token_hash = NULL
            WHERE user_id = %s
            """,
            (user_id,),
        )

    print(
        "REPAIRED AGENT:",
        user_id,
        agent_address,
    )

    return {
        "repaired": True,
        "agent_address": agent_address,
    }

@app.post("/users/register")
def register_user(
    request: Request,
    req: RegisterUserRequest,
    x_internal_auth: Optional[str] = Header(None),
):
    identity = req.google_id or req.x_id or req.email or "unknown"
    rate_limit(
        request,
        limit=5,
        window=60,
        identity=identity,
    )
    require_internal_auth(x_internal_auth)

    with get_conn() as conn:
        if req.provider == "twitter":
            if not req.x_id:
                raise HTTPException(
                    status_code=400,
                    detail="x_id is required for Twitter registration",
                )
            conn.execute(
                """
                SELECT
                    id,
                    wallet_address,
                    agent_address,
                    permissions_confirmed
                FROM users
                WHERE x_id = %s OR email = %s
                """,
                (req.x_id, req.email),
            )
        else:
            if not req.google_id or not req.email:
                raise HTTPException(
                    status_code=400,
                    detail="google_id and email are required for Google registration",
                )
            conn.execute(
                """
                SELECT
                    id,
                    wallet_address,
                    agent_address,
                    permissions_confirmed
                FROM users
                WHERE google_id = %s OR email = %s
                """,
                (req.google_id, req.email),
            )

        existing = conn.fetchone()

        # Existing account.
        if existing:
            api_key, api_key_hash = generate_api_key()

            conn.execute(
                """
                UPDATE users
                SET
                    google_id = %s,
                    x_id = %s,
                    email = %s,
                    name = %s,
                    picture = %s,
                    provider = %s,
                    provider_id = %s,
                    api_key_hash = %s
                WHERE id = %s
                """,
                (
                    req.google_id,
                    req.x_id,
                    req.email,
                    req.name,
                    req.picture,
                    req.provider,
                    req.google_id or req.x_id,
                    api_key_hash,
                    existing["id"],
                ),
            )
            return {
                "user_id": existing["id"],
                "new_user": False,
                "api_key": api_key,
                "wallet_connected": bool(existing["wallet_address"]),
                "agent_created": bool(existing["agent_address"]),
                "permissions_approved": bool(
                    existing["permissions_confirmed"]
                ),
            }

        # Brand-new account.
        user_id = str(uuid.uuid4())

        conn.execute(
            """
            INSERT INTO users (
                id,
                google_id,
                provider_id,
                email,
                name,
                picture,
                provider,
                x_id,
                wallet_address,
                agent_address,
                agent_key_encrypted,
                api_key_hash
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, NULL, NULL)
            """,
            (
                user_id,
                req.google_id,
                req.google_id or req.x_id,
                req.email,
                req.name,
                req.picture,
                req.provider,
                req.x_id,
            ),
        )

        return {
            "user_id": user_id,
            "new_user": True,
            "api_key": None,
        }

@app.post("/wallet/confirm-permissions")
def confirm_permissions(
    request: Request,
    req: ConfirmPermissionsRequest,
    authorization: Optional[str] = Header(None),
):
    rate_limit(
        request,
        limit=5,
        window=60,
        identity=req.user_id,
    )
    _require_agent_auth(
        req.user_id,
        authorization,
    )

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE users
            SET permissions_confirmed = 1
            WHERE id = %s
            """,
            (req.user_id,),
        )
    return {"confirmed": True}


def _get_user(user_id: str):
    with get_conn() as conn:
        conn.execute(
            "SELECT * FROM users WHERE id=%s",
            (user_id,),
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
    return user


def _require_agent_auth(
    user_id: str,
    authorization: Optional[str],
    connection=None,
):
    user = _get_user(user_id)
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="missing Authorization header",
        )
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="invalid Authorization header",
        )
    credential = authorization.removeprefix("Bearer ").strip()
    if user["api_key_hash"] and verify_api_key(
        credential,
        user["api_key_hash"],
    ):
        user["auth_role"] = "user"
        return user
    token_hash = hash_agent_token(credential)
    with get_conn() as conn:
        conn.execute(
            """
            SELECT ac.user_id, u.*
            FROM agent_connections ac
            JOIN users u ON u.id=ac.user_id
            WHERE ac.user_id=%s
              AND ac.agent_token_hash=%s
              AND ac.connected=1
            """,
            (user_id, token_hash),
        )
        connection = conn.fetchone()
    if connection is None:
        raise HTTPException(
            status_code=401,
            detail="invalid API key or agent token",
        )
    connection["auth_role"] = "agent"
    return connection


def _mark_agent_active(user_id: str):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE users
            SET
                last_seen=CURRENT_TIMESTAMP,
                permissions_confirmed=1
            WHERE id=%s
            """,
            (user_id,),
        )
