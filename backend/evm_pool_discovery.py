from __future__ import annotations

from dataclasses import asdict, dataclass
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

    def as_dict(self):
        return asdict(self)


def checksum(address: str) -> str:
    if not Web3.is_address(address):
        raise ValueError(f"Invalid EVM address: {address}")
    return Web3.to_checksum_address(address)


def discover_v3_pools(
    w3: Web3,
    factory_address: str,
    token_in: str,
    token_out: str,
    fees: tuple[int, ...],
) -> list[V3Pool]:
    if not factory_address:
        raise ValueError("UNISWAP_V3_FACTORY is not configured.")

    factory = w3.eth.contract(
        address=checksum(factory_address),
        abi=V3_FACTORY_ABI,
    )

    token_in = checksum(token_in)
    token_out = checksum(token_out)
    result: list[V3Pool] = []

    for fee in fees:
        address = factory.functions.getPool(token_in, token_out, fee).call()

        if int(address, 16) == 0:
            continue

        pool = w3.eth.contract(
            address=checksum(address),
            abi=V3_POOL_ABI,
        )

        liquidity = pool.functions.liquidity().call()
        sqrt_price_x96, tick, *_ = pool.functions.slot0().call()

        if liquidity <= 0:
            continue

        result.append(
            V3Pool(
                address=checksum(address),
                token_in=token_in,
                token_out=token_out,
                fee=fee,
                liquidity=liquidity,
                sqrt_price_x96=sqrt_price_x96,
                tick=tick,
            )
        )

    return result


def choose_deepest_pool(pools: list[V3Pool]) -> Optional[V3Pool]:
    return max(pools, key=lambda p: p.liquidity) if pools else None
