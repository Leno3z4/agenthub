"""
Quote validation layer.

The first version uses the Uniswap v3 Quoter contract supplied by configuration.
It never sends a transaction and never signs anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from web3 import Web3


QUOTER_V2_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "internalType": "struct IQuoterV2.QuoteExactInputSingleParams",
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"},
            {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"},
            {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


@dataclass(frozen=True)
class Quote:
    amount_in: int
    amount_out: int
    minimum_amount_out: int
    token_in: str
    token_out: str
    fee: int
    gas_estimate: int


def _addr(value: str) -> str:
    if not Web3.is_address(value):
        raise ValueError(f"Invalid address: {value}")
    return Web3.to_checksum_address(value)


def quote_exact_input_single(
    w3: Web3,
    quoter_address: str,
    token_in: str,
    token_out: str,
    amount_in: int,
    fee: int,
    slippage_bps: int = 100,
) -> Quote:
    if amount_in <= 0:
        raise ValueError("amount_in must be positive")
    if not 0 <= slippage_bps <= 5000:
        raise ValueError("slippage_bps must be between 0 and 5000")

    quoter = w3.eth.contract(
        address=_addr(quoter_address),
        abi=QUOTER_V2_ABI,
    )

    amount_out, _, _, gas_estimate = quoter.functions.quoteExactInputSingle(
        (
            _addr(token_in),
            _addr(token_out),
            amount_in,
            fee,
            0,
        )
    ).call()

    minimum_amount_out = (
        amount_out * (10_000 - slippage_bps) // 10_000
    )

    return Quote(
        amount_in=amount_in,
        amount_out=amount_out,
        minimum_amount_out=minimum_amount_out,
        token_in=_addr(token_in),
        token_out=_addr(token_out),
        fee=fee,
        gas_estimate=gas_estimate,
    )
