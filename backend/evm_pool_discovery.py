"""
Arc/Uniswap pool discovery primitives.

This module deliberately separates discovery from transaction execution.
It supports Uniswap v3 factory discovery and a pluggable v4 index source.

For v4, on-chain PoolManager does not expose a simple "find pools for token"
enumeration method. A production indexer should consume PoolInitialize events
and persist PoolKey metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from web3 import Web3


V3_FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]

V3_POOL_ABI = [
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


@dataclass(frozen=True)
class V3Pool:
    address: str
    token_in: str
    token_out: str
    fee: int
    liquidity: int
    sqrt_price_x96: int
    tick: int


def _addr(value: str) -> str:
    if not Web3.is_address(value):
        raise ValueError(f"Invalid address: {value}")
    return Web3.to_checksum_address(value)


def discover_v3_pools(
    w3: Web3,
    factory_address: str,
    token_a: str,
    token_b: str,
    fees: tuple[int, ...] = (100, 500, 3000, 10000),
) -> list[V3Pool]:
    factory = w3.eth.contract(
        address=_addr(factory_address),
        abi=V3_FACTORY_ABI,
    )

    pools: list[V3Pool] = []

    for fee in fees:
        pool_address = factory.functions.getPool(
            _addr(token_a),
            _addr(token_b),
            fee,
        ).call()

        if int(pool_address, 16) == 0:
            continue

        pool = w3.eth.contract(
            address=_addr(pool_address),
            abi=V3_POOL_ABI,
        )

        liquidity = pool.functions.liquidity().call()
        sqrt_price_x96, tick, *_ = pool.functions.slot0().call()

        if liquidity == 0:
            continue

        pools.append(
            V3Pool(
                address=_addr(pool_address),
                token_in=_addr(token_a),
                token_out=_addr(token_b),
                fee=fee,
                liquidity=liquidity,
                sqrt_price_x96=sqrt_price_x96,
                tick=tick,
            )
        )

    return pools


def choose_deepest_v3_pool(pools: list[V3Pool]) -> Optional[V3Pool]:
    if not pools:
        return None
    return max(pools, key=lambda pool: pool.liquidity)
