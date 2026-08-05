from pathlib import Path
from typing import Optional
import uuid

from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from db import init_db, get_conn
from crypto_utils import encrypt, decrypt
from auth import generate_api_key, verify_api_key

from hl_client import (
    generate_agent_wallet,
    get_account_state,
    execute_trade,
    execute_close,
    get_markets,
)

from bridge import (
    deposit_parameters,
    bridge_status,
)

from config import ARC_CCTP_DOMAIN, CORS_ORIGINS

from agent_session import (
    create_session,
    validate_session,
    touch_session,
    destroy_session,
)

app = FastAPI(title="Alias Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
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
# Wallet linking and registration
# ---------------------------------------------------------------------


def wallet_link_message(user_id: str, wallet_address: str) -> str:
    return "\n".join(
        [
            "Alias wallet link",
            f"User: {user_id}",
            f"Wallet: {wallet_address}",
        ]
    )


class LinkWalletRequest(BaseModel):
    user_id: str
    wallet_address: str
    message: str
    signature: str


class LinkWalletResponse(BaseModel):
    agent_address: str
    api_key: str


@app.post("/wallet/link", response_model=LinkWalletResponse)
def link_wallet(req: LinkWalletRequest):
    # The browser may provide a wallet address, but it must prove control of
    # that address. Profile and provider identity come from registration, not
    # mutable client-supplied fields.
    expected_message = wallet_link_message(req.user_id, req.wallet_address)
    if req.message != expected_message:
        raise HTTPException(status_code=400, detail="invalid wallet link message")

    try:
        recovered = Account.recover_message(
            encode_defunct(text=req.message),
            signature=req.signature,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid wallet signature") from exc

    if recovered.lower() != req.wallet_address.lower():
        raise HTTPException(status_code=401, detail="wallet signature does not match address")

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (req.user_id,),
        ).fetchone()

        if existing is None:
            raise HTTPException(status_code=404, detail="User must register first.")

        if (
            existing["wallet_address"] is not None
            and existing["wallet_address"].lower() != req.wallet_address.lower()
        ):
            raise HTTPException(
                status_code=409,
                detail="This account already has a different wallet linked.",
            )

        api_key, api_key_hash = generate_api_key()

        if existing["agent_address"]:
            conn.execute(
                """
                UPDATE users
                SET wallet_address = ?, api_key_hash = ?
                WHERE id = ?
                """,
                (req.wallet_address, api_key_hash, req.user_id),
            )
            return LinkWalletResponse(
                agent_address=existing["agent_address"],
                api_key=api_key,
            )

        agent_address, agent_private_key = generate_agent_wallet()
        conn.execute(
            """
            UPDATE users
            SET wallet_address = ?, agent_address = ?,
                agent_key_encrypted = ?, api_key_hash = ?
            WHERE id = ?
            """,
            (
                req.wallet_address,
                agent_address,
                encrypt(agent_private_key),
                api_key_hash,
                req.user_id,
            ),
        )

        return LinkWalletResponse(
            agent_address=agent_address,
            api_key=api_key,
        )


class ConfirmPermissionsRequest(BaseModel):
    user_id: str


class RegisterUserRequest(BaseModel):
    provider: str = "google"
    provider_id: Optional[str] = None
    # Kept as a compatibility alias for existing clients.
    google_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None


@app.post("/users/register")
def register_user(req: RegisterUserRequest):
    provider_id = req.provider_id or req.google_id
    if not provider_id:
        raise HTTPException(status_code=422, detail="provider_id is required")

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE google_id = ?",
            (provider_id,),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE users
                SET auth_provider = ?, email = ?, name = ?, picture = ?
                WHERE id = ?
                """,
                (
                    req.provider,
                    req.email,
                    req.name,
                    req.picture,
                    existing["id"],
                ),
            )
            return {"user_id": existing["id"], "new_user": False}

        user_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO users (
                id, google_id, auth_provider, email, name, picture,
                wallet_address, agent_address, agent_key_encrypted, api_key_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)
            """,
            (
                user_id,
                provider_id,
                req.provider,
                req.email,
                req.name,
                req.picture,
            ),
        )
        return {"user_id": user_id, "new_user": True}


@app.post("/wallet/confirm-permissions")
def confirm_permissions(
    req: ConfirmPermissionsRequest,
    authorization: Optional[str] = Header(None),
):
    _require_agent_auth(req.user_id, authorization)

    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET permissions_confirmed = 1 WHERE id = ?",
            (req.user_id,),
        )

    return {"confirmed": True}


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------


def _get_user(user_id: str):
    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    if user is None:
        raise HTTPException(status_code=404, detail="wallet not linked")

    return user


def _require_agent_auth(user_id: str, authorization: Optional[str]):
    user = _get_user(user_id)

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="invalid Authorization header")

    api_key = authorization.removeprefix("Bearer ").strip()
    if not verify_api_key(api_key, user["api_key_hash"]):
        raise HTTPException(status_code=401, detail="invalid API key")

    return user


def _mark_agent_active(user_id: str):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE users
            SET last_seen = CURRENT_TIMESTAMP, permissions_confirmed = 1
            WHERE id = ?
            """,
            (user_id,),
        )


# ---------------------------------------------------------------------
# Agent status
# ---------------------------------------------------------------------

@app.get("/users/{user_id}/agent/status")
def agent_status(
    user_id: str,
    authorization: Optional[str] = Header(None),
):
    user = _require_agent_auth(user_id, authorization)

    with get_conn() as conn:
        last_trade = conn.execute(
            """
            SELECT * FROM trades
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user["id"],),
        ).fetchone()

    connected = False
    if user["last_seen"]:
        with get_conn() as conn:
            row = conn.execute(
                """
                SELECT (julianday('now') - julianday(?)) * 24 * 60 AS minutes_ago
                """,
                (user["last_seen"],),
            ).fetchone()
        connected = row["minutes_ago"] is not None and row["minutes_ago"] < 10

    return {
        "wallet_connected": True,
        "permissions_approved": bool(user["permissions_confirmed"]),
        "agent_connected": connected,
        "last_seen": user["last_seen"],
        "latest_action": dict(last_trade) if last_trade else None,
    }


# ---------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------

class DepositParamsRequest(BaseModel):
    amount_usdc_units: int


class DepositCompleteRequest(BaseModel):
    user_id: str
    burn_tx_hash: str
    amount_usdc_units: int


@app.post("/bridge/deposit-params")
def bridge_deposit_params(req: DepositParamsRequest):
    return deposit_parameters(req.amount_usdc_units)


@app.post("/bridge/deposit")
def bridge_deposit(
    req: DepositCompleteRequest,
    authorization: Optional[str] = Header(None),
):
    user = _require_agent_auth(req.user_id, authorization)

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO bridge_transfers (user_id, amount_usdc, burn_tx_hash, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                user["id"],
                req.amount_usdc_units / 1_000_000,
                req.burn_tx_hash,
                "pending",
            ),
        )

    return {"accepted": True, "burn_tx_hash": req.burn_tx_hash}


@app.get("/bridge/status/{burn_tx_hash}")
def bridge_transfer_status(burn_tx_hash: str):
    return bridge_status(ARC_CCTP_DOMAIN, burn_tx_hash)


# ---------------------------------------------------------------------
# Markets and trade execution
# ---------------------------------------------------------------------

@app.get("/markets")
def markets():
    return get_markets()


class TradeRequest(BaseModel):
    coin: str
    is_buy: bool
    size: float
    leverage: Optional[int] = None
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    strategy: Optional[str] = None


@app.post("/users/{user_id}/trade")
def agent_trade(
    user_id: str,
    req: TradeRequest,
    authorization: Optional[str] = Header(None),
):
    user = _require_agent_auth(user_id, authorization)
    agent_private_key = decrypt(user["agent_key_encrypted"])
    result = execute_trade(
        agent_private_key=agent_private_key,
        coin=req.coin,
        is_buy=req.is_buy,
        size=req.size,
        leverage=req.leverage,
    )
    _mark_agent_active(user_id)

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO trades
            (user_id, coin, is_buy, size, result, reasoning, confidence, model, strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"], req.coin, int(req.is_buy), req.size, str(result),
                req.reasoning, req.confidence, req.model, req.strategy,
            ),
        )
    return result


class CloseRequest(BaseModel):
    coin: str
    size: Optional[float] = None
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    strategy: Optional[str] = None


@app.post("/users/{user_id}/close")
def agent_close(
    user_id: str,
    req: CloseRequest,
    authorization: Optional[str] = Header(None),
):
    user = _require_agent_auth(user_id, authorization)
    agent_private_key = decrypt(user["agent_key_encrypted"])
    result = execute_close(
        agent_private_key=agent_private_key,
        coin=req.coin,
        size=req.size,
    )
    _mark_agent_active(user_id)

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO trades
            (user_id, coin, is_buy, size, result, reasoning, confidence, model, strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"], req.coin, 0, req.size or 0, str(result),
                req.reasoning, req.confidence, req.model, req.strategy,
            ),
        )
    return result


# ---------------------------------------------------------------------
# Dashboard and agent sessions
# ---------------------------------------------------------------------

@app.get("/users/{user_id}/dashboard")
def dashboard(
    user_id: str,
    authorization: Optional[str] = Header(None),
):
    user = _require_agent_auth(user_id, authorization)
    return get_account_state(user["wallet_address"])


class AgentConnectRequest(BaseModel):
    user_id: str


class AgentConnectResponse(BaseModel):
    session_token: str
    base_url: str


class AgentHeartbeatRequest(BaseModel):
    session_token: str


class AgentDisconnectRequest(BaseModel):
    session_token: str


@app.post("/agent/connect", response_model=AgentConnectResponse)
def agent_connect(
    request: Request,
    req: AgentConnectRequest,
    authorization: Optional[str] = Header(None),
):
    _require_agent_auth(req.user_id, authorization)
    session_token = create_session(authorization.removeprefix("Bearer ").strip())
    return AgentConnectResponse(
        session_token=session_token,
        base_url=str(request.base_url).rstrip("/"),
    )


@app.post("/agent/heartbeat")
def agent_heartbeat(req: AgentHeartbeatRequest):
    if not validate_session(req.session_token):
        raise HTTPException(401, "Session expired.")
    touch_session(req.session_token)
    return {"alive": True}


@app.post("/agent/disconnect")
def agent_disconnect(req: AgentDisconnectRequest):
    destroy_session(req.session_token)
    return {"success": True}
