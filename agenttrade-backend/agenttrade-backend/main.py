from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import init_db, get_conn
from crypto_utils import encrypt, decrypt
from hl_client import generate_agent_wallet, get_account_state, execute_trade, execute_close, get_markets
from bridge import burn_on_arc, fetch_attestation, mint_on_hyperevm
from config import HYPERLIQUID_CCTP_DOMAIN, HL_API_URL, CCTP_MESSAGE_TRANSMITTER_HL

app = FastAPI(title="AgentTrade Backend")

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


@app.post("/agents/{arc_address}/trade")
def agent_trade(arc_address: str, req: TradeRequest):
    user = _get_user(arc_address)
    agent_key = decrypt(user["agent_key_encrypted"])

    result = execute_trade(agent_key, req.coin, req.is_buy, req.size, req.leverage)

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO trades (user_id, coin, is_buy, size, result) VALUES (?, ?, ?, ?, ?)",
            (user["id"], req.coin, int(req.is_buy), req.size, str(result)),
        )
    return result


class CloseRequest(BaseModel):
    coin: str
    size: Optional[float] = None  # omit to close the full position


@app.post("/agents/{arc_address}/close")
def agent_close(arc_address: str, req: CloseRequest):
    user = _get_user(arc_address)
    agent_key = decrypt(user["agent_key_encrypted"])

    result = execute_close(agent_key, req.coin, req.size)

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO trades (user_id, coin, is_buy, size, result) VALUES (?, ?, ?, ?, ?)",
            (user["id"], req.coin, 0, req.size or 0, str(result)),
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
