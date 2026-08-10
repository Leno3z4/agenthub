"""
Hyperliquid execution backend.

The user's real wallet never signs trades directly.
Alias generates one delegated signing key per user and the user
approves that address once through Hyperliquid's approveAgent action.

The delegated agent can trade, but cannot withdraw user funds.
"""

from typing import Optional
import time

from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange

from config import HL_API_URL


def generate_agent_wallet() -> tuple[str, str]:
    acct = Account.create()
    return acct.address, acct.key.hex()


def get_exchange_for_agent(
    agent_private_key: str,
    account_address: str,
) -> Exchange:
    if not agent_private_key:
        raise ValueError("Agent private key is missing.")

    if not account_address:
        raise ValueError("Hyperliquid account address is missing.")

    wallet = Account.from_key(agent_private_key)

    return Exchange(
        wallet,
        HL_API_URL,
        account_address=account_address,
    )


def _validate_address(user_address: str) -> str:
    if not user_address:
        raise ValueError("Hyperliquid account address is missing.")

    user_address = user_address.strip()

    if not user_address.startswith("0x") or len(user_address) != 42:
        raise ValueError(
            f"Invalid Hyperliquid account address: {user_address!r}"
        )

    try:
        int(user_address[2:], 16)
    except ValueError:
        raise ValueError(
            f"Invalid Hyperliquid account address: {user_address!r}"
        )

    return user_address

def get_authorized_agents(user_address: str) -> list[dict]:
    info = Info(
        HL_API_URL,
        skip_ws=True,
    )

    return info.extra_agents(user_address)

def is_agent_authorized(
    user_address: str,
    agent_address: str,
) -> bool:
    if not user_address or not agent_address:
        return False

    try:
        agents = get_authorized_agents(user_address)
    except Exception as exc:
        print("HYPERLIQUID AGENT CHECK FAILED:", repr(exc))
        return False

    now = int(time.time() * 1000)

    return any(
        agent.get("address", "").lower() == agent_address.lower()
        and (
            agent.get("validUntil") is None
            or agent["validUntil"] > now
        )
        for agent in agents
    )


def get_account_state(user_address: str) -> dict:
    """
    Read Hyperliquid perpetual + spot USDC state.
    """

    user_address = _validate_address(user_address)

    info = Info(
        HL_API_URL,
        skip_ws=True,
    )

    state = info.post(
        "/info",
        {
            "type": "clearinghouseState",
            "user": user_address,
            "dex": "",
        },
    )

    spot_state = info.post(
        "/info",
        {
            "type": "spotClearinghouseState",
            "user": user_address,
        },
    )

    usdc_total = 0.0
    usdc_hold = 0.0

    for balance in spot_state.get("balances", []):
        if balance.get("coin") == "USDC":
            usdc_total = float(
                balance.get("total", 0)
            )
            usdc_hold = float(
                balance.get("hold", 0)
            )
            break

    margin = state.get("marginSummary", {})

    return {
        "account_value": margin.get(
            "accountValue",
            "0",
        ),
        "margin_used": margin.get(
            "totalMarginUsed",
            "0",
        ),
        "withdrawable": state.get(
            "withdrawable",
            "0",
        ),

        "usdc_balance": str(
            usdc_total
        ),

        "usdc_available": str(
            max(
                0.0,
                usdc_total - usdc_hold,
            )
        ),

        "spot_usdc_balance": str(
            usdc_total
        ),

        "spot_usdc_available": str(
            max(
                0.0,
                usdc_total - usdc_hold,
            )
        ),

        "positions": [
            p["position"]
            for p in state.get(
                "assetPositions",
                [],
            )
        ],
    }


def get_markets() -> list[dict]:
    """
    Full universe of tradable perp markets.
    """

    info = Info(
        HL_API_URL,
        skip_ws=True,
    )

    meta, asset_ctxs = info.meta_and_asset_ctxs()

    return [
        {
            "coin": asset["name"],
            "max_leverage": asset["maxLeverage"],
            "mark_price": ctx.get("markPx"),
            "prev_day_price": ctx.get("prevDayPx"),
            "funding_rate": ctx.get("funding"),
            "open_interest": ctx.get("openInterest"),
            "day_volume": ctx.get("dayNtlVlm"),
        }
        for asset, ctx in zip(
            meta["universe"],
            asset_ctxs,
        )
    ]


def get_market_candles(
    coin: str,
    interval: str = "1h",
    hours: int = 48,
) -> list[dict]:

    end_time = int(
        time.time() * 1000
    )

    start_time = (
        end_time
        - max(1, hours)
        * 60
        * 60
        * 1000
    )

    info = Info(
        HL_API_URL,
        skip_ws=True,
    )

    candles = info.post(
        "/info",
        {
            "type": "candleSnapshot",
            "req": {
                "coin": coin.upper(),
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time,
            },
        },
    )

    return [
        {
            "time": c["t"],
            "open": c["o"],
            "high": c["h"],
            "low": c["l"],
            "close": c["c"],
        }
        for c in candles
    ]


def execute_trade(
    agent_private_key: str,
    account_address: str,
    coin: str,
    is_buy: bool,
    size: float,
    leverage: int | None = None,
    slippage: float = 0.01,
) -> dict:

    exchange = get_exchange_for_agent(
        agent_private_key,
        account_address,
    )

    if leverage is not None:
        exchange.update_leverage(
            leverage,
            coin,
        )

    return exchange.market_open(
        name=coin,
        is_buy=is_buy,
        sz=size,
        slippage=slippage,
    )


def execute_close(
    agent_private_key: str,
    account_address: str,
    coin: str,
    size: Optional[float] = None,
    slippage: float = 0.01,
) -> dict:

    exchange = get_exchange_for_agent(
        agent_private_key,
        account_address,
    )

    return exchange.market_close(
        coin,
        size,
        None,
        slippage,
    )
