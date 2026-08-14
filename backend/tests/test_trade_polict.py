import pytest

from evm_trade_policy import TradePolicy, validate_trade


def test_trade_policy_accepts_valid_trade():
    validate_trade(
        amount_in=100,
        minimum_amount_out=98,
        amount_out=100,
        pool_liquidity=1_000_000,
        policy=TradePolicy(max_slippage_bps=300),
    )


def test_trade_policy_rejects_low_liquidity():
    with pytest.raises(ValueError):
        validate_trade(
            amount_in=100,
            minimum_amount_out=98,
            amount_out=100,
            pool_liquidity=0,
            policy=TradePolicy(min_pool_liquidity=1),
        )


def test_trade_policy_rejects_large_trade():
    with pytest.raises(ValueError):
        validate_trade(
            amount_in=1000,
            minimum_amount_out=980,
            amount_out=1000,
            pool_liquidity=1_000_000,
            policy=TradePolicy(max_trade_raw=500),
        )
