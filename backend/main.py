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
    google_id: str
    email: str
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
    rate_limit(
        request,
        limit=5,
        window=60,
        identity=req.google_id,
    )
    require_internal_auth(x_internal_auth)

    with get_conn() as conn:
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
                    email = %s,
                    name = %s,
                    picture = %s,
                    api_key_hash = %s
                WHERE id = %s
                """,
                (
                    req.google_id,
                    req.email,
                    req.name,
                    req.picture,
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, NULL, NULL, NULL, NULL)
            """,
            (
                user_id,
                req.google_id,
                req.google_id,
                req.email,
                req.name,
                req.picture,
                req.provider,
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
            WHERE id =  %s
            """,
            (req.user_id,),
        )

    return {
        "confirmed": True,
    }
# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _get_user(user_id: str):

    with get_conn() as conn:
        conn.execute(
            """
            SELECT *
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

    # Browser/user authentication: API key.
    if user["api_key_hash"] and verify_api_key(
        credential,
        user["api_key_hash"],
    ):
        user["auth_role"] = "user"
        return user

    # Agent authentication: hashed agent bearer token.
    token_hash = hash_agent_token(credential)

    with get_conn() as conn:
        conn.execute(
            """
            SELECT
                ac.user_id,
                u.*
            FROM agent_connections ac
            JOIN users u
                ON u.id = ac.user_id
            WHERE ac.user_id = %s
              AND ac.agent_token_hash = %s
              AND ac.connected = 1
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



def _mark_agent_active(
    user_id: str,
):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE users
            SET
                last_seen = CURRENT_TIMESTAMP,
                permissions_confirmed = 1
            WHERE id = %s
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
    user = _require_agent_auth(
        user_id,
        authorization,
    )

    with get_conn() as conn:
        conn.execute(
            """
            SELECT *
            FROM trades
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (user["id"],),
        )
        last_trade = conn.fetchone()

    connected = False

    if user["last_seen"]:
        with get_conn() as conn:
            conn.execute(
                """
                SELECT connected, connected_at
                FROM agent_connections
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (user["id"],),
            )
            connection = conn.fetchone()
    
        connected = bool(
            connection
            and connection["connected"]
        )


    return {
        "wallet_connected": True,
        "permissions_approved": bool(
            user["permissions_confirmed"]
        ),
        "agent_connected": connected,
        "last_seen": user["last_seen"],
        "latest_action": (
            dict(last_trade)
            if last_trade
            else None
        ),
    }
# ---------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------


class DepositParamsRequest(BaseModel):
    amount: int
    hypercore_recipient: str

class DepositCompleteRequest(BaseModel):
    user_id: str
    burn_tx_hash: str
    amount_usdc_units: int

class WithdrawalParametersRequest(BaseModel):
    user_id: str
    amount: str
    destination: str


class WithdrawalConfirmRequest(BaseModel):
    user_id: str
    withdrawal_id: str
    amount: str
    destination: str
    hyperliquid_amount: str
    source_dex: str = ""
    hyperliquid_result: dict | None = None


@app.post("/bridge/deposit-params")
def bridge_deposit_params(
    req: DepositParamsRequest,
):
    """
    Returns everything the frontend needs before calling
    depositForBurn() from the user's wallet.
    """

    return deposit_parameters(
        req.amount,
        req.hypercore_recipient,
    )


@app.post("/bridge/deposit")
def bridge_deposit(
    request: Request,
    req: DepositCompleteRequest,
    authorization: Optional[str] = Header(None),
):
    rate_limit(
        request,
        limit=5,
        window=60,
        identity=req.user_id,
    )
    """
    Called after the user's wallet successfully broadcasts
    depositForBurn(). The backend simply records the bridge
    request; Circle and HyperCore handle the rest.
    """

    user = _require_agent_auth(
        req.user_id,
        authorization,
    )

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO bridge_transfers
            (
                user_id,
                amount_usdc,
                status,
                withdrawal_id,
                destination,
                relay_destination
            )
            VALUES (%s, %s, %s, NULL, NULL, NULL)
            """,
            (
                user["id"],
                req.amount_usdc_units / 1_000_000,
                "pending",
            ),
        )

    return {
        "accepted": True,
        "burn_tx_hash": req.burn_tx_hash,
        "status": "pending",
    }


@app.get("/bridge/status/{burn_tx_hash}")
def bridge_transfer_status(
    burn_tx_hash: str,
):
    return bridge_status(
        ARC_CCTP_DOMAIN,
        burn_tx_hash,
    )




@app.post("/bridge/withdraw-params")
def get_withdrawal_parameters(
    request: Request,
    req: WithdrawalParametersRequest,
    authorization: Optional[str] = Header(None),
):
    rate_limit(
        request,
        limit=10,
        window=60,
        identity=req.user_id,
    )
    user = _require_agent_auth(
        req.user_id,
        authorization,
    )

    if user.get("auth_role") == "agent":
        raise HTTPException(
            status_code=403,
            detail="Agents cannot access withdrawal parameters.",
        )

    try:
        return create_withdrawal(
            user_address=user["wallet_address"],
            amount=req.amount,
            arc_destination=req.destination,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    except Exception as exc:
        print("WITHDRAWAL PARAMETER ERROR:", repr(exc))
        raise HTTPException(
            status_code=502,
            detail="Unable to calculate current withdrawal fees.",
        )


@app.post("/bridge/withdraw")
def submit_withdrawal(
    request: Request,
    req: WithdrawalConfirmRequest,
    authorization: Optional[str] = Header(None),
):
    rate_limit(
        request,
        limit=3,
        window=60,
        identity=req.user_id,
    )
    user = _require_agent_auth(
        req.user_id,
        authorization,
    )

    if user.get("auth_role") == "agent":
        raise HTTPException(
            status_code=403,
            detail="Agents cannot execute withdrawals.",
        )

    try:
        destination = req.destination.strip()

        if destination.lower() != str(
            user["wallet_address"]
        ).lower():
            raise ValueError(
                "Withdrawal destination does not match the linked wallet."
            )

        if not req.withdrawal_id:
            raise ValueError(
                "Withdrawal ID is required."
            )
        
        result = process_withdrawal(
            withdrawal_id=req.withdrawal_id,
            hyperliquid_amount=req.hyperliquid_amount,
            arc_destination=destination,
            source_dex=req.source_dex,
            hyperliquid_result=req.hyperliquid_result,
        )
        
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO bridge_transfers
                (
                    user_id,
                    amount_usdc,
                    status,
                    withdrawal_id,
                    destination,
                    relay_destination
                )
                VALUES (%s, %s, %s, %s, %s, NULL)
                ON CONFLICT DO NOTHING
                """,
                (
                    user["id"],
                    float(req.amount),
                    result["status"],
                    req.withdrawal_id,
                    destination,
                ),
            )
        return {
            "accepted": True,
            "withdrawal_id": req.withdrawal_id,
            "status": result["status"],
            "route": result["route"],
            "source_dex": req.source_dex,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    except Exception as exc:
        print(
            "WITHDRAWAL RECORDING FAILED:",
            req.withdrawal_id,
            repr(exc),
        )
        raise HTTPException(
            status_code=500,
            detail="Withdrawal was submitted but could not be recorded.",
        )


@app.get("/bridge/withdraw/status/{burn_tx_hash}")
def get_withdrawal_status(
    burn_tx_hash: str,
):
    try:
        return withdrawal_status(burn_tx_hash)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )


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
    request: Request,
    user_id: str,
    req: TradeRequest,
    authorization: Optional[str] = Header(None),
):
    rate_limit(
        request,
        limit=10,
        window=60,
        identity=user_id,
    )

    user = _require_agent_auth(
        user_id,
        authorization,
    )
    if not req.coin.strip():
        raise HTTPException(
            status_code=400,
            detail="Coin is required.",
        )
    
    if req.size <= 0:
        raise HTTPException(
            status_code=400,
            detail="Trade size must be greater than zero.",
        )
    
    markets = get_markets()
    
    market = next(
        (
            m
            for m in markets
            if str(m["coin"]).upper()
            == req.coin.strip().upper()
        ),
        None,
    )
    
    if market is None:
        raise HTTPException(
            status_code=400,
            detail="Unknown or unsupported market.",
        )
    
    mark_price = float(market.get("mark_price") or 0)
    
    if mark_price <= 0:
        raise HTTPException(
            status_code=503,
            detail="Market price is currently unavailable.",
        )
    
    notional = req.size * mark_price
    
    if notional > MAX_TRADE_NOTIONAL:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Trade notional ${notional:.2f} exceeds "
                f"the ${MAX_TRADE_NOTIONAL:.2f} maximum."
            ),
        )
    
    if req.leverage is not None:
        if req.leverage <= 0:
            raise HTTPException(
                status_code=400,
                detail="Leverage must be greater than zero.",
            )
    
        max_leverage = int(market.get("max_leverage") or 0)
    
        if max_leverage > 0 and req.leverage > max_leverage:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Maximum leverage for {market['coin']} "
                    f"is {max_leverage}x."
                ),
            )
    if not req.coin.strip():
        raise HTTPException(
            status_code=400,
            detail="Coin is required.",
        )
    
    if req.size <= 0:
        raise HTTPException(
            status_code=400,
            detail="Trade size must be greater than zero.",
        )
    
    if req.leverage is not None and req.leverage <= 0:
        raise HTTPException(
            status_code=400,
            detail="Leverage must be greater than zero.",
        )
    
    if req.confidence is not None and not 0 <= req.confidence <= 1:
        raise HTTPException(
            status_code=400,
            detail="Confidence must be between 0 and 1.",
        )
    if not user["agent_key_encrypted"]:
        raise HTTPException(
            status_code=409,
            detail="Agent signing key is missing. Repair the agent.",
        )
    
    try:
        agent_private_key = decrypt(
            user["agent_key_encrypted"]
        )
    except Exception as exc:
        print(
            "AGENT KEY DECRYPTION FAILED:",
            repr(exc),
        )
        raise HTTPException(
            status_code=409,
            detail="Stored agent signing key cannot be decrypted. Repair the agent.",
        )
    
    try:
        derived_address = Account.from_key(
            agent_private_key
        ).address
    except Exception as exc:
        print(
            "AGENT KEY INVALID:",
            repr(exc),
        )
        raise HTTPException(
            status_code=409,
            detail="Stored agent signing key is invalid. Repair the agent.",
        )
    
    if derived_address.lower() != user["agent_address"].lower():
        print(
            "AGENT KEY/ADDRESS MISMATCH:",
            user["agent_address"],
            derived_address,
        )
    
        raise HTTPException(
            status_code=409,
            detail="Stored agent key does not match the agent address. Repair the agent.",
        )
    
    if not is_agent_authorized(
        user["wallet_address"],
        user["agent_address"],
    ):
        raise HTTPException(
            status_code=409,
            detail="Agent is not authorized by Hyperliquid. Authorize the agent from your wallet.",
        )

    result = execute_trade(
        agent_private_key=agent_private_key,
        account_address=user["wallet_address"],
        coin=req.coin,
        is_buy=req.is_buy,
        size=req.size,
        leverage=req.leverage,
    )

    _mark_agent_active(
        user_id,
    )

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO trades
            (
                user_id,
                coin,
                is_buy,
                size,
                result,
                reasoning,
                confidence,
                model,
                strategy
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user["id"],
                req.coin,
                int(req.is_buy),
                req.size,
                str(result),
                req.reasoning,
                req.confidence,
                req.model,
                req.strategy,
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
    request: Request,
    user_id: str,
    req: CloseRequest,
    authorization: Optional[str] = Header(None),
):
    rate_limit(
        request,
        limit=10,
        window=60,
        identity=user_id,
    )
    user = _require_agent_auth(
        user_id,
        authorization,
    )

    agent_private_key = decrypt(
        user["agent_key_encrypted"],
    )

    result = execute_close(
        agent_private_key=agent_private_key,
        account_address=user["wallet_address"],
        coin=req.coin,
        size=req.size,
    )

    _mark_agent_active(
        user_id,
    )

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO trades
            (
                user_id,
                coin,
                is_buy,
                size,
                result,
                reasoning,
                confidence,
                model,
                strategy
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user["id"],
                req.coin,
                0,
                req.size or 0,
                str(result),
                req.reasoning,
                req.confidence,
                req.model,
                req.strategy,
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
    """
    Returns the user's current HyperCore / Hyperliquid account state.
    """

    user = _require_agent_auth(
        user_id,
        authorization,
    )
    
    return get_account_state(
        user["wallet_address"],
    )

@app.post("/agent/connect", response_model=AgentConnectResponse)
def agent_connect(
    request: Request,
    req: AgentConnectRequest,
    authorization: Optional[str] = Header(None),
):
    rate_limit(
        request,
        limit=5,
        window=60,
        identity=req.user_id,
    )
    """
    Called once by the agent after the user pastes the skill.
    Exchanges the API key for a long-lived session token.
    """

    _require_agent_auth(
        req.user_id,
        authorization,
    )

    session_token = create_session(
        authorization.removeprefix("Bearer ").strip()
    )

    return AgentConnectResponse(
        session_token=session_token,
        base_url=str(request.base_url).rstrip("/"),
    )

@app.post("/agent/heartbeat")
def agent_heartbeat(
    request: Request,
    req: AgentHeartbeatRequest,
):
    rate_limit(
        request,
        limit=30,
        window=60,
        identity=req.session_token,
    )
    if not validate_session(req.session_token):
        raise HTTPException(
            401,
            "Session expired.",
        )

    touch_session(req.session_token)

    return {
        "alive": True,
    }

@app.post("/agent/disconnect")
def agent_disconnect(
    request: Request,
    req: AgentDisconnectRequest,
):
    rate_limit(
        request,
        limit=5,
        window=60,
        identity=req.session_token,
    )
    destroy_session(req.session_token)

    return {
        "success": True,
    }
