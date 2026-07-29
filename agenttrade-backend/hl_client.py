"""
Hyperliquid is the execution backend. The user's real wallet never signs
trades directly — instead, the platform generates ONE delegated signing
key per user, and the user approves that address ONCE from their own
wallet via Hyperliquid's `approve_agent` action (done client-side, not
here — see frontend notes in README). That approval grants trading
rights only; it structurally cannot withdraw funds.
"""

from typing import Optional
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from config import HL_API_URL


def generate_agent_wallet() -> tuple[str, str]:
    """Create the keypair the platform will hold for this user.
    Returns (address, private_key_hex). The address is what the user
    must approve via approve_agent from their own wallet."""
    acct = Account.create()
    return acct.address, acct.key.hex()


def get_exchange_for_agent(agent_private_key: str) -> Exchange:
    wallet = Account.from_key(agent_private_key)
    return Exchange(wallet, HL_API_URL)


def get_account_state(user_address: str) -> dict:
    """Reads the MASTER account's state — same address on Arc and
    Hyperliquid since both are EVM (secp256k1) chains."""
    info = Info(HL_API_URL, skip_ws=True)
    state = info.user_state(user_address)
    return {
        "account_value": state["marginSummary"]["accountValue"],
        "margin_used": state["marginSummary"]["totalMarginUsed"],
        "positions": [p["position"] for p in state["assetPositions"]],
    }


def get_markets() -> list[dict]:
    """Full universe of tradable perp markets, live from Hyperliquid.
    This is what an agent should call to discover what's tradable —
    not something a human copy-pastes per token."""
    info = Info(HL_API_URL, skip_ws=True)
    meta, asset_ctxs = info.meta_and_asset_ctxs()
    markets = []
    for asset, ctx in zip(meta["universe"], asset_ctxs):
        markets.append({
            "coin": asset["name"],
            "max_leverage": asset["maxLeverage"],
            "mark_price": ctx.get("markPx"),
            "prev_day_price": ctx.get("prevDayPx"),
            "funding_rate": ctx.get("funding"),
            "open_interest": ctx.get("openInterest"),
            "day_volume": ctx.get("dayNtlVlm"),
        })
    return markets


def execute_close(
    agent_private_key: str,
    coin: str,
    size: Optional[float] = None,
    slippage: float = 0.01,
) -> dict:
    """Closes an open position (fully, or partially if size is given).
    This is the other half of execute_trade — an agent needs both to
    actually be autonomous: open when it sees an opportunity, close
    when it decides it's done."""
    exchange = get_exchange_for_agent(agent_private_key)
    return exchange.market_close(coin, size, None, slippage)

