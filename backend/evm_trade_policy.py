from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TradePolicy:
    max_slippage_bps: int = 300
    max_price_impact_bps: int = 1000
    min_pool_liquidity: int = 1
    max_trade_raw: int = 0


def validate_trade(
    *,
    amount_in: int,
    minimum_amount_out: int,
    amount_out: int,
    pool_liquidity: int,
    policy: TradePolicy,
) -> None:
    if amount_in <= 0:
        raise ValueError("Trade amount must be positive.")

    if pool_liquidity < policy.min_pool_liquidity:
        raise ValueError("Pool liquidity is below the configured minimum.")

    if minimum_amount_out <= 0 or amount_out <= 0:
        raise ValueError("Invalid quote.")

    if policy.max_trade_raw and amount_in > policy.max_trade_raw:
        raise ValueError("Trade exceeds configured maximum.")

    effective_slippage_bps = (
        (amount_out - minimum_amount_out) * 10_000 // amount_out
    )

    if effective_slippage_bps > policy.max_slippage_bps:
        raise ValueError("Configured slippage exceeds trade policy.")
