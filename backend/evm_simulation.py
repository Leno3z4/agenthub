from __future__ import annotations

from typing import Any

from web3 import Web3


def simulate_transaction(
    w3: Web3,
    transaction: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute an eth_call against the current chain state.

    This does not broadcast a transaction and does not consume funds.
    It catches reverted swaps before the signing stage.
    """
    result = w3.eth.call(transaction)

    return {
        "ok": True,
        "return_data": result.hex(),
    }


def estimate_gas(
    w3: Web3,
    transaction: dict[str, Any],
) -> int:
    return w3.eth.estimate_gas(transaction)
