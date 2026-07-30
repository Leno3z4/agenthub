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
    """Read the master account's Hyperliquid perpetual state.

    Uses the raw /info endpoint so read-only account queries do not
    depend on the SDK's spot metadata initialization.
    """
    import requests

    response = requests.post(
        f"{HL_API_URL}/info",
        json={
            "type": "clearinghouseState",
            "user": user_address,
        },
        timeout=30,
    )
    response.raise_for_status()

    state = response.json()
    margin_summary = state.get("marginSummary", {})

    return {
        "account_value": margin_summary.get("accountValue"),
        "margin_used": margin_summary.get("totalMarginUsed"),
        "positions": [
            p["position"]
            for p in state.get("assetPositions", [])
        ],
    }


def get_markets() -> list[dict]:
    """Return all tradable Hyperliquid perpetual markets.

    Uses the raw /info endpoint instead of constructing the SDK Info
    client, because the SDK constructor can fail while loading spot
    metadata even though perp metadata is available.
    """
    import requests

    response = requests.post(
        f"{HL_API_URL}/info",
        json={"type": "metaAndAssetCtxs"},
        timeout=30,
    )
    response.raise_for_status()

    meta, asset_ctxs = response.json()
    markets = []

    for asset, ctx in zip(meta.get("universe", []), asset_ctxs):
        markets.append({
            "coin": asset["name"],
            "max_leverage": asset.get("maxLeverage"),
            "mark_price": ctx.get("markPx"),
            "prev_day_price": ctx.get("prevDayPx"),
            "funding_rate": ctx.get("funding"),
            "open_interest": ctx.get("openInterest"),
            "day_volume": ctx.get("dayNtlVlm"),
        })

    return markets

def execute_trade(
    agent_private_key: str,
    coin: str,
    is_buy: bool,
    size: float,
    leverage: int | None = None,
    slippage: float = 0.01,
) -> dict:
    exchange = get_exchange_for_agent(agent_private_key)

    if leverage is not None:
        exchange.update_leverage(leverage, coin)

    return exchange.market_open(
        name=coin,
        is_buy=is_buy,
        sz=size,
        slippage=slippage,
    )


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

