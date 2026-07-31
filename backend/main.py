from typing import Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from db import init_db, get_conn
from crypto_utils import encrypt, decrypt
from hl_client import generate_agent_wallet, get_account_state, execute_trade, execute_close, get_markets
from bridge import burn_on_arc, fetch_attestation, mint_on_hyperevm
from config import HYPERLIQUID_CCTP_DOMAIN, HL_API_URL, CCTP_MESSAGE_TRANSMITTER_HL

app = FastAPI(title="Alias Backend")

# Dev-friendly for now (allows your local frontend + Vercel preview URLs).
# Tighten this to your actual domain before going live.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# ---------------------------------------------------------------------
# Skill — the single URL a user pastes into their coding agent's chat.
# It reads this, learns the API, and starts operating on its own —
# same mechanic as dev.fun Arena's agent skill files.
# ---------------------------------------------------------------------

SKILL_TEXT = Path(__file__).parent.joinpath("ALIAS_SKILL.md").read_text()


@app.get("/skill", response_class=PlainTextResponse)
def skill(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return SKILL_TEXT.replace("{base_url}", base_url)


@app.get("/", response_class=PlainTextResponse)
def root():
    return "Alias backend is live. Paste /skill into your agent's chat to get started."


# ---------------------------------------------------------------------
# Wallet linking — generates the delegated agent key for this user.
# The user still has to approve this address from THEIR OWN wallet via
# Hyperliquid's approve_agent action, in the frontend — this endpoint
# only prepares the address for them to approve.
# ---------------------------------------------------------------------

class LinkWalletRequest(BaseModel):
    arc_address: str


class LinkWalletResponse(BaseModel):
    agent_address: str


@app.post("/wallet/link", response_model=LinkWalletResponse)
def link_wallet(req: LinkWalletRequest):
    agent_address, agent_key = generate_agent_wallet()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO users (arc_address, agent_address, agent_key_encrypted) "
            "VALUES (?, ?, ?)",
            (req.arc_address, agent_address, encrypt(agent_key)),
        )
    return LinkWalletResponse(agent_address=agent_address)


def _get_user(arc_address: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE arc_address = ?", (arc_address,)).fetchone()
    if not row:
        raise HTTPException(404, "wallet not linked — call /wallet/link first")
    return row


def _mark_agent_active(arc_address: str):
    """Called on every successful trade/close. A successful call could
    only happen if approve_agent actually went through, so this also
    confirms permissions even if the explicit confirm step was skipped."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET last_seen = CURRENT_TIMESTAMP, permissions_confirmed = 1 "
            "WHERE arc_address = ?",
            (arc_address,),
        )


class ConfirmPermissionsRequest(BaseModel):
    arc_address: str


@app.post("/wallet/confirm-permissions")
def confirm_permissions(req: ConfirmPermissionsRequest):
    """The frontend calls this right after the user completes the
    approve_agent signature in their wallet. Purely a status flag for
    the dashboard — trades still work without ever calling this,
    since _mark_agent_active confirms it automatically too."""
    _get_user(req.arc_address)
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET permissions_confirmed = 1 WHERE arc_address = ?",
            (req.arc_address,),
        )
    return {"confirmed": True}


@app.get("/agents/{arc_address}/status")
def agent_status(arc_address: str):
    """Powers the monitoring dashboard: connection state, permission
    state, and the most recent thing the agent actually did — real
    data, not placeholders."""
    user = _get_user(arc_address)

    with get_conn() as conn:
        last_trade = conn.execute(
            "SELECT * FROM trades WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user["id"],),
        ).fetchone()

    agent_connected = False
    if user["last_seen"]:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT (julianday('now') - julianday(?)) * 24 * 60 AS minutes_ago",
                (user["last_seen"],),
            ).fetchone()
        agent_connected = row["minutes_ago"] is not None and row["minutes_ago"] < 10

    return {
        "wallet_connected": True,
        "permissions_approved": bool(user["permissions_confirmed"]),
        "agent_connected": agent_connected,
        "last_seen": user["last_seen"],
        "latest_action": dict(last_trade) if last_trade else None,
    }


# ---------------------------------------------------------------------
# Bridge — moves USDC from the user's Arc balance to their Hyperliquid
# margin account so trades have funds to execute against.
# ---------------------------------------------------------------------

class BridgeRequest(BaseModel):
    arc_address: str
    user_private_key: str   # signs the burn tx client-side in a real deploy — see README
    amount_usdc_units: int  # smallest unit, 6 decimals (5 USDC = 5_000_000)


@app.post("/bridge/deposit")
def bridge_deposit(req: BridgeRequest):
    user = _get_user(req.arc_address)

    burn_hash = burn_on_arc(req.user_private_key, req.amount_usdc_units, req.arc_address)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO bridge_transfers (user_id, amount_usdc, burn_tx_hash, status) "
            "VALUES (?, ?, ?, 'pending')",
            (user["id"], req.amount_usdc_units / 1_000_000, burn_hash),
        )

    attestation = fetch_attestation(int(HYPERLIQUID_CCTP_DOMAIN or 0), burn_hash)

    mint_hash = mint_on_hyperevm(
        relayer_private_key=req.user_private_key,  # simplest option: self-relay for now
        hl_rpc_url=HL_API_URL,
        message_transmitter=CCTP_MESSAGE_TRANSMITTER_HL,
        message_hex=attestation["message"],
        attestation_hex=attestation["attestation"],
    )

    with get_conn() as conn:
        conn.execute(
            "UPDATE bridge_transfers SET status = 'minted' WHERE burn_tx_hash = ?", (burn_hash,)
        )

    return {"burn_tx": burn_hash, "mint_tx": mint_hash}


# ---------------------------------------------------------------------
# Markets — the agent calls this to discover what's tradable, on its
# own. No human hands it a token; it pulls the live universe itself.
# ---------------------------------------------------------------------

@app.get("/markets")
def markets():
    return get_markets()


# ---------------------------------------------------------------------
# Trade execution — what the user's connected AI agent calls.
# ---------------------------------------------------------------------

class TradeRequest(BaseModel):
    coin: str
    is_buy: bool
    size: float
    leverage: Optional[int] = None
    reasoning: Optional[str] = None   # optional — powers the "latest agent action" display
    confidence: Optional[float] = None
    model: Optional[str] = None
    strategy: Optional[str] = None


@app.post("/agents/{arc_address}/trade")
def agent_trade(arc_address: str, req: TradeRequest):
    user = _get_user(arc_address)
    agent_key = decrypt(user["agent_key_encrypted"])

    result = execute_trade(agent_key, req.coin, req.is_buy, req.size, req.leverage)
    _mark_agent_active(arc_address)

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO trades (user_id, coin, is_buy, size, result, reasoning, confidence, model, strategy) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user["id"], req.coin, int(req.is_buy), req.size, str(result),
             req.reasoning, req.confidence, req.model, req.strategy),
        )
    return result


class CloseRequest(BaseModel):
    coin: str
    size: Optional[float] = None  # omit to close the full position
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    strategy: Optional[str] = None


@app.post("/agents/{arc_address}/close")
def agent_close(arc_address: str, req: CloseRequest):
    user = _get_user(arc_address)
    agent_key = decrypt(user["agent_key_encrypted"])

    result = execute_close(agent_key, req.coin, req.size)
    _mark_agent_active(arc_address)

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO trades (user_id, coin, is_buy, size, result, reasoning, confidence, model, strategy) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user["id"], req.coin, 0, req.size or 0, str(result),
             req.reasoning, req.confidence, req.model, req.strategy),
        )
    return result


# ---------------------------------------------------------------------
# Dashboard — positions, margin, P&L. Public Hyperliquid read, no auth
# needed on their side; you gate it with your own auth in front of this.
# ---------------------------------------------------------------------

@app.get("/dashboard/{arc_address}")
def dashboard(arc_address: str):
    _get_user(arc_address)  # 404s if not linked
    return get_account_state(arc_address)
