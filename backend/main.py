from pathlib import Path
from typing import Optional
import logging
import secrets
import sqlite3
import time
import uuid

from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from web3 import Web3

from db import init_db, get_conn
from crypto_utils import encrypt, decrypt
from auth import (
    generate_api_key,
    verify_api_key,
    generate_nonce,
    hash_nonce,
    verify_google_id_token,
)

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

from config import (
    HYPERLIQUID_CCTP_DOMAIN,
    ARC_CCTP_DOMAIN,
    ALLOWED_ORIGINS,
)

from agent_session import (
    create_session,
    validate_session,
    touch_session,
    destroy_session,
)

logger = logging.getLogger("alias.auth")

app = FastAPI(title="Alias Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
    wallet_address: str
    nonce: str
    signature: str
    # Retained for request compatibility only. These fields are never used
    # for identity; the verified Google token is the sole identity source.
    google_id: str | None = None
    email: str | None = None
    name: str | None = None
    picture: str | None = None


class WalletNonceRequest(BaseModel):
    user_id: str
    wallet_address: str


class LinkWalletResponse(BaseModel):
    agent_address: str
    api_key: str


def wallet_link_message(user_id: str, wallet_address: str, nonce: str) -> str:
    return "\n".join(
        [
            "Alias wallet link",
            f"User: {user_id}",
            f"Wallet: {wallet_address}",
            f"Nonce: {nonce}",
        ]
    )


def _bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return token


def _verified_google_user(user_id: str | None, authorization: Optional[str]):
    """Authenticate Google, then resolve the account from the verified sub.

    The client may send a legacy user_id for API compatibility, but it is
    checked against the account selected by the verified Google subject and is
    never used as the identity source.
    """
    try:
        claims = verify_google_id_token(_bearer_token(authorization))
    except (ValueError, RuntimeError) as exc:
        logger.warning("authentication_failed method=google")
        raise HTTPException(status_code=401, detail="Authentication failed.") from exc

    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE google_id = ?",
            (claims["sub"],),
        ).fetchone()

    if user is None:
        logger.warning("authentication_failed method=google reason=account_not_found")
        raise HTTPException(status_code=404, detail="Account not found.")

    if user_id is not None and user["id"] != user_id:
        logger.warning("authentication_failed method=google reason=account_mismatch")
        raise HTTPException(status_code=403, detail="Account access denied.")

    return user, claims


@app.post("/wallet/nonce")
def wallet_nonce(
    req: WalletNonceRequest,
    authorization: Optional[str] = Header(None),
):
    # A nonce is issued only after the Google token has selected the account.
    user, _ = _verified_google_user(req.user_id, authorization)

    if not Web3.is_address(req.wallet_address):
        logger.warning("authentication_failed method=wallet reason=invalid_address")
        raise HTTPException(status_code=400, detail="Invalid wallet address.")

    nonce = generate_nonce()
    now = int(time.time())
    expires_at = now + 600
    wallet_address = req.wallet_address.lower()
    message = wallet_link_message(user["id"], wallet_address, nonce)

    with get_conn() as conn:
        # A newer attempt invalidates older unused attempts for this account
        # and wallet, limiting the number of valid authentication challenges.
        conn.execute(
            """
            UPDATE wallet_nonces
            SET used_at = ?
            WHERE user_id = ? AND wallet_address = ? AND used_at IS NULL
            """,
            (now, user["id"], wallet_address),
        )
        conn.execute(
            """
            INSERT INTO wallet_nonces
            (user_id, wallet_address, nonce_hash, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                wallet_address,
                hash_nonce(nonce),
                expires_at,
                now,
            ),
        )

    return {
        "nonce": nonce,
        "message": message,
        "expires_at": expires_at,
    }


@app.post("/wallet/link", response_model=LinkWalletResponse)
def link_wallet(
    req: LinkWalletRequest,
    authorization: Optional[str] = Header(None),
):
    # Both factors are mandatory: the verified Google identity selects the
    # account, while the signed nonce proves control of the wallet.
    user, _ = _verified_google_user(req.user_id, authorization)

    if not Web3.is_address(req.wallet_address):
        logger.warning("authentication_failed method=wallet reason=invalid_address")
        raise HTTPException(status_code=400, detail="Invalid wallet address.")

    wallet_address = req.wallet_address.lower()
    message = wallet_link_message(user["id"], wallet_address, req.nonce)

    try:
        recovered = Account.recover_message(
            encode_defunct(text=message),
            signature=req.signature,
        )
    except Exception as exc:
        logger.warning("authentication_failed method=wallet reason=invalid_signature")
        raise HTTPException(
            status_code=401,
            detail="Wallet authentication failed.",
        ) from exc

    if not secrets.compare_digest(recovered.lower(), wallet_address):
        logger.warning("authentication_failed method=wallet reason=signer_mismatch")
        raise HTTPException(status_code=401, detail="Wallet authentication failed.")

    now = int(time.time())
    try:
        with get_conn() as conn:
            # The nonce is hashed at rest and consumed atomically immediately
            # after signature verification, preventing replay.
            nonce_row = conn.execute(
                """
                SELECT id
                FROM wallet_nonces
                WHERE user_id = ?
                  AND wallet_address = ?
                  AND nonce_hash = ?
                  AND used_at IS NULL
                  AND expires_at > ?
                """,
                (
                    user["id"],
                    wallet_address,
                    hash_nonce(req.nonce),
                    now,
                ),
            ).fetchone()

            if nonce_row is None:
                logger.warning("authentication_failed method=wallet reason=invalid_nonce")
                raise HTTPException(
                    status_code=401,
                    detail="Wallet authentication failed.",
                )

            consumed = conn.execute(
                """
                UPDATE wallet_nonces
                SET used_at = ?
                WHERE id = ? AND used_at IS NULL AND expires_at > ?
                """,
                (now, nonce_row["id"], now),
            ).rowcount

            if consumed != 1:
                logger.warning("authentication_failed method=wallet reason=nonce_replay")
                raise HTTPException(
                    status_code=401,
                    detail="Wallet authentication failed.",
                )

            existing = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user["id"],),
            ).fetchone()

            if existing is None:
                logger.warning("authentication_failed method=wallet reason=account_not_found")
                raise HTTPException(status_code=404, detail="Account not found.")

            # Do not rely on the database UNIQUE constraint for this check:
            # return a safe authentication response instead of leaking a 500
            # if a wallet is already controlled by another account.
            wallet_owner = conn.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(wallet_address) = ? AND id != ?
                LIMIT 1
                """,
                (wallet_address, user["id"]),
            ).fetchone()
            if wallet_owner is not None:
                logger.warning("authentication_failed method=wallet reason=wallet_already_linked")
                raise HTTPException(status_code=409, detail="Wallet is already linked.")

            if (
                existing["wallet_address"] is not None
                and existing["wallet_address"].lower() != wallet_address
            ):
                raise HTTPException(
                    status_code=409,
                    detail="A different wallet is already linked.",
                )

            api_key, api_key_hash = generate_api_key()

            if existing["agent_address"]:
                conn.execute(
                    "UPDATE users SET wallet_address = ?, api_key_hash = ? WHERE id = ?",
                    (wallet_address, api_key_hash, user["id"]),
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
                    wallet_address,
                    agent_address,
                    encrypt(agent_private_key),
                    api_key_hash,
                    user["id"],
                ),
            )

            return LinkWalletResponse(
                agent_address=agent_address,
                api_key=api_key,
            )
    except sqlite3.IntegrityError as exc:
        # A concurrent link can race the preflight ownership check. Keep that
        # failure generic and non-sensitive rather than returning a DB error.
        logger.warning("authentication_failed method=wallet reason=ownership_race")
        raise HTTPException(status_code=409, detail="Wallet is already linked.") from exc


class ConfirmPermissionsRequest(BaseModel):
    user_id: str


class RegisterUserRequest(BaseModel):
    id_token: str | None = None
    provider: str = "google"
    # Retained for request compatibility, but never trusted for identity.
    google_id: str | None = None
    email: str | None = None
    name: str | None = None
    picture: str | None = None


@app.post("/users/register")
def register_user(req: RegisterUserRequest):
    """Register or refresh an account from a verified Google ID token only."""
    if req.provider != "google":
        raise HTTPException(status_code=400, detail="Google authentication is required.")

    try:
        claims = verify_google_id_token(req.id_token or "")
    except (ValueError, RuntimeError) as exc:
        logger.warning("authentication_failed method=google reason=registration")
        raise HTTPException(status_code=401, detail="Authentication failed.") from exc

    # These values are read only after google-auth has verified signature,
    # issuer, audience, expiry, subject, and email verification.
    google_id = claims["sub"]
    email = claims["email"]
    name = claims.get("name")
    picture = claims.get("picture")

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE google_id = ?",
            (google_id,),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE users
                SET email = ?, name = ?, picture = ?
                WHERE google_id = ?
                """
                ,
                (email, name, picture, google_id),
            )
            return {"user_id": existing["id"], "new_user": False}

        email_owner = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if email_owner:
            logger.warning("authentication_failed method=google reason=email_conflict")
            raise HTTPException(status_code=409, detail="Account already exists.")

        user_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO users (
                id, google_id, email, name, picture,
                wallet_address, agent_address, agent_key_encrypted, api_key_hash
            )
            VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)
            """,
            (user_id, google_id, email, name, picture),
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
        return conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def _require_agent_auth(
    user_id: str,
    authorization: Optional[str],
):
    # Parse the credential before looking up the account and use the same
    # response for missing, invalid, and unknown credentials. This prevents
    # protected endpoints from leaking whether a user ID exists.
    api_key = _bearer_token(authorization)
    user = _get_user(user_id)

    if user is None or not verify_api_key(api_key, user["api_key_hash"]):
        logger.warning("authentication_failed method=api_key")
        raise HTTPException(status_code=401, detail="Authentication failed.")

    return user


def _mark_agent_active(
    user_id: str,
):
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
            SELECT *
            FROM trades
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
                SELECT
                    (julianday('now') - julianday(?))
                    * 24
                    * 60
                    AS minutes_ago
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
            INSERT INTO bridge_transfers
            (user_id, amount_usdc, burn_tx_hash, status)
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
# Markets
# ---------------------------------------------------------------------

@app.get("/markets")
def markets():
    return get_markets()


# ---------------------------------------------------------------------
# Trade execution
# ---------------------------------------------------------------------

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


class AgentConnectRequest(BaseModel):
    user_id: str


class AgentConnectResponse(BaseModel):
    session_token: str
    base_url: str


class AgentHeartbeatRequest(BaseModel):
    session_token: str


class AgentDisconnectRequest(BaseModel):
    session_token: str


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
# Dashboard
# ---------------------------------------------------------------------

@app.get("/users/{user_id}/dashboard")
def dashboard(
    user_id: str,
    authorization: Optional[str] = Header(None),
):
    user = _require_agent_auth(user_id, authorization)
    return get_account_state(user["wallet_address"])


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
