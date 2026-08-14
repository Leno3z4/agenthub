from __future__ import annotations

import time
from dataclasses import dataclass

from web3 import Web3

from evm_pool_discovery import checksum


ERC20_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

SWAP_ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "internalType": "struct ISwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "exactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function",
    }
]


@dataclass(frozen=True)
class SwapBuild:
    transaction: dict


def _base_tx(w3: Web3, sender: str) -> dict:
    sender = checksum(sender)
    return {
        "from": sender,
        "chainId": w3.eth.chain_id,
        "nonce": w3.eth.get_transaction_count(sender, "pending"),
    }


def build_approval(
    w3: Web3,
    token: str,
    owner: str,
    spender: str,
    amount: int,
) -> dict:
    if amount <= 0:
        raise ValueError("Approval amount must be positive.")

    contract = w3.eth.contract(
        address=checksum(token),
        abi=ERC20_ABI,
    )

    return contract.functions.approve(
        checksum(spender),
        amount,
    ).build_transaction(_base_tx(w3, owner))


def get_allowance(
    w3: Web3,
    token: str,
    owner: str,
    spender: str,
) -> int:
    contract = w3.eth.contract(
        address=checksum(token),
        abi=ERC20_ABI,
    )

    return contract.functions.allowance(
        checksum(owner),
        checksum(spender),
    ).call()


def build_exact_input_single(
    w3: Web3,
    router_address: str,
    token_in: str,
    token_out: str,
    fee: int,
    recipient: str,
    amount_in: int,
    amount_out_minimum: int,
    deadline_seconds: int = 60,
) -> dict:
    if not router_address:
        raise ValueError("UNISWAP_V3_SWAP_ROUTER is not configured.")
    if amount_in <= 0:
        raise ValueError("amount_in must be positive.")
    if amount_out_minimum <= 0:
        raise ValueError("amount_out_minimum must be positive.")

    router = w3.eth.contract(
        address=checksum(router_address),
        abi=SWAP_ROUTER_ABI,
    )

    params = (
        checksum(token_in),
        checksum(token_out),
        fee,
        checksum(recipient),
        int(time.time()) + deadline_seconds,
        amount_in,
        amount_out_minimum,
        0,
    )

    tx = router.functions.exactInputSingle(params).build_transaction(
        {
            **_base_tx(w3, recipient),
            "value": 0,
        }
    )

    return tx
