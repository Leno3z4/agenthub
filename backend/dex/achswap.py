from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from web3 import Web3

from evm.rpc import checksum_address
from evm.erc20 import allowance, build_approval

ACHSWAP_ADAPTER = "0xF82c88FbF46E109a3865647E5c4d4834b31f8AFB"
ACHSWAP_CHAIN_ID = 5042002

ADAPTER_ABI = [
    {"inputs":[{"name":"tokenIn","type":"address"},{"name":"tokenOut","type":"address"},{"name":"amountIn","type":"uint256"}],"name":"quote","outputs":[{"name":"expectedOut","type":"uint256"},{"name":"routeData","type":"bytes"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"quotedOut","type":"uint256"},{"name":"slippageBps","type":"uint16"}],"name":"minOut","outputs":[{"name":"","type":"uint256"}],"stateMutability":"pure","type":"function"},
    {"inputs":[{"name":"tokenIn","type":"address"},{"name":"tokenOut","type":"address"},{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"recipient","type":"address"},{"name":"routeData","type":"bytes"}],"name":"swap","outputs":[{"name":"totalOut","type":"uint256"}],"stateMutability":"payable","type":"function"},
]

@dataclass(frozen=True)
class AchSwapQuote:
    token_in: str
    token_out: str
    amount_in: int
    expected_out: int
    minimum_out: int
    route_data: str


def adapter(w3: Web3):
    return w3.eth.contract(
        address=checksum_address(w3, ACHSWAP_ADAPTER),
        abi=ADAPTER_ABI,
    )


def quote(w3: Web3, token_in: str, token_out: str, amount_in: int, slippage_bps: int = 100) -> AchSwapQuote:
    if w3.eth.chain_id != ACHSWAP_CHAIN_ID:
        raise RuntimeError(f"AchSwap requires chain {ACHSWAP_CHAIN_ID}")
    if amount_in <= 0:
        raise ValueError("amount_in must be greater than zero")
    if not 0 <= slippage_bps <= 10_000:
        raise ValueError("slippage_bps must be between 0 and 10000")

    token_in = checksum_address(w3, token_in)
    token_out = checksum_address(w3, token_out)
    expected_out, route_data = adapter(w3).functions.quote(token_in, token_out, amount_in).call()
    minimum_out = adapter(w3).functions.minOut(expected_out, slippage_bps).call()

    return AchSwapQuote(token_in, token_out, amount_in, expected_out, minimum_out, Web3.to_hex(route_data))


def build_approval_if_needed(w3: Web3, owner: str, token_in: str, amount_in: int):
    current = allowance(w3, token_in, owner, ACHSWAP_ADAPTER)
    if current >= amount_in:
        return None
    return build_approval(w3, token_in, owner, ACHSWAP_ADAPTER, amount_in)


def build_swap(w3: Web3, owner: str, q: AchSwapQuote) -> dict[str, Any]:
    owner = checksum_address(w3, owner)
    fn = adapter(w3).functions.swap(
        q.token_in, q.token_out, q.amount_in, q.minimum_out, owner, Web3.to_bytes(hexstr=q.route_data)
    )
    is_native = q.token_in == "0x0000000000000000000000000000000000000000"
    return fn.build_transaction({
        "from": owner,
        "chainId": w3.eth.chain_id,
        "nonce": w3.eth.get_transaction_count(owner, "pending"),
        "value": q.amount_in if is_native else 0,
    })

