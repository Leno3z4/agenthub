"""
EVM spot execution adapter for Alias.

Phase 1 targets Arc and keeps execution isolated from Hyperliquid.
The adapter discovers a Uniswap v4 pool from a supplied pool key,
reads pool state, and prepares a Universal Router swap transaction.

No private keys are persisted here. Signing remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from eth_account import Account
from web3 import Web3


ARC_CHAIN_ID = 5042
ARC_RPC_URL = "https://rpc.arc.network"

USDC = Web3.to_checksum_address(
    "0x3600000000000000000000000000000000000000"
)

UNIVERSAL_ROUTER = Web3.to_checksum_address(
    "0x4fca4a51ab4f23a7447b3284fbd7d73289a89fb1"
)

PERMIT2 = Web3.to_checksum_address(
    "0x000000000022D473030F116dDEE9F6B43aC78BA3"
)

# Minimal ERC20 ABI needed by the execution layer.
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

STATE_VIEW_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "poolId", "type": "bytes32"}],
        "name": "getSlot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint24", "name": "protocolFee", "type": "uint24"},
            {"internalType": "uint24", "name": "lpFee", "type": "uint24"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "poolId", "type": "bytes32"}],
        "name": "getLiquidity",
        "outputs": [{"internalType": "uint128", "name": "liquidity", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    },
]


@dataclass(frozen=True)
class PoolKey:
    currency0: str
    currency1: str
    fee: int
    tick_spacing: int
    hooks: str


@dataclass(frozen=True)
class TradeQuote:
    token_in: str
    token_out: str
    amount_in: int
    amount_out_minimum: int
    pool_id: str
    liquidity: int
    sqrt_price_x96: int
    tick: int


def get_web3(rpc_url: str = ARC_RPC_URL) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        raise RuntimeError("Unable to connect to Arc RPC.")
    return w3


def normalize_address(address: str) -> str:
    if not Web3.is_address(address):
        raise ValueError(f"Invalid EVM address: {address!r}")
    return Web3.to_checksum_address(address)


def pool_id(pool: PoolKey) -> bytes:
    """
    Uniswap v4 PoolId = keccak256(abi.encode(PoolKey)).
    """
    return Web3.solidity_keccak(
        ["address", "address", "uint24", "int24", "address"],
        [
            normalize_address(pool.currency0),
            normalize_address(pool.currency1),
            pool.fee,
            pool.tick_spacing,
            normalize_address(pool.hooks),
        ],
    )


def read_pool_state(
    w3: Web3,
    state_view_address: str,
    pool: PoolKey,
) -> dict[str, Any]:
    """
    Read v4 pool state. state_view_address must be the StateView deployment
    for the selected chain.
    """
    pid = pool_id(pool)
    contract = w3.eth.contract(
        address=normalize_address(state_view_address),
        abi=STATE_VIEW_ABI,
    )

    sqrt_price_x96, tick, protocol_fee, lp_fee = contract.functions.getSlot0(
        pid
    ).call()
    liquidity = contract.functions.getLiquidity(pid).call()

    return {
        "pool_id": Web3.to_hex(pid),
        "sqrt_price_x96": sqrt_price_x96,
        "tick": tick,
        "protocol_fee": protocol_fee,
        "lp_fee": lp_fee,
        "liquidity": liquidity,
    }


def token_contract(w3: Web3, token: str):
    return w3.eth.contract(address=normalize_address(token), abi=ERC20_ABI)


def get_balance(w3: Web3, token: str, owner: str) -> int:
    return token_contract(w3, token).functions.balanceOf(
        normalize_address(owner)
    ).call()


def get_allowance(w3: Web3, token: str, owner: str, spender: str) -> int:
    return token_contract(w3, token).functions.allowance(
        normalize_address(owner),
        normalize_address(spender),
    ).call()


def build_erc20_approval(
    w3: Web3,
    token: str,
    owner: str,
    spender: str,
    amount: int,
) -> dict[str, Any]:
    contract = token_contract(w3, token)
    return contract.functions.approve(
        normalize_address(spender),
        amount,
    ).build_transaction(
        {
            "from": normalize_address(owner),
            "chainId": ARC_CHAIN_ID,
            "nonce": w3.eth.get_transaction_count(
                normalize_address(owner),
                "pending",
            ),
        }
    )


def build_swap_transaction(
    w3: Web3,
    owner: str,
    commands: bytes,
    inputs: list[bytes],
    value: int = 0,
) -> dict[str, Any]:
    """
    Build (but do not sign/send) a Universal Router execute transaction.

    `commands` and `inputs` must be produced by a tested Uniswap Universal
    Router command encoder. Keeping encoding outside this function makes
    the adapter easy to test and prevents accidental transaction submission.
    """
    router_abi = [
        {
            "inputs": [
                {"internalType": "bytes", "name": "commands", "type": "bytes"},
                {"internalType": "bytes[]", "name": "inputs", "type": "bytes[]"},
            ],
            "name": "execute",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function",
        },
    ]

    router = w3.eth.contract(
        address=UNIVERSAL_ROUTER,
        abi=router_abi,
    )

    return router.functions.execute(
        commands,
        inputs,
    ).build_transaction(
        {
            "from": normalize_address(owner),
            "value": value,
            "chainId": ARC_CHAIN_ID,
            "nonce": w3.eth.get_transaction_count(
                normalize_address(owner),
                "pending",
            ),
        }
    )


def sign_transaction(
    private_key: str,
    transaction: dict[str, Any],
) -> dict[str, Any]:
    """
    Local signing helper. The caller is responsible for deciding whether a
    transaction is allowed to be signed.
    """
    account = Account.from_key(private_key)
    if normalize_address(transaction["from"]) != account.address:
        raise ValueError("Transaction sender does not match signing key.")

    tx = dict(transaction)
    if "gas" not in tx:
        tx["gas"] = 500_000

    if "maxFeePerGas" not in tx and "gasPrice" not in tx:
        tx["gasPrice"] = 0

    signed = account.sign_transaction(tx)
    return {
        "raw_transaction": signed.raw_transaction.hex(),
        "hash": signed.hash.hex(),
    }


def send_signed_transaction(
    w3: Web3,
    raw_transaction: str,
) -> str:
    tx_hash = w3.eth.send_raw_transaction(bytes.fromhex(raw_transaction.removeprefix("0x")))
    return tx_hash.hex()
