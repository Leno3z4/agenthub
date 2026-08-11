"""
Alias withdrawal flow.

Flow:

Hyperliquid HyperCore
        |
        | withdraw3
        v
Hyperliquid withdrawal destination
        |
        v
Circle CCTP
        |
        v
Arc
        |
        v
User's Arc wallet

This module only handles backend-side withdrawal
configuration/status helpers.

The actual Hyperliquid withdraw3 transaction is signed
and submitted by the frontend.
"""

from __future__ import annotations

import requests

from config import (
    CCTP_IRIS_API,
    ARC_CCTP_DOMAIN,
    HYPERLIQUID_CCTP_DOMAIN,
    require,
)


def address_to_bytes32(address: str) -> str:
    address = address.removeprefix("0x")

    if len(address) != 40:
        raise ValueError("Invalid EVM address")

    try:
        int(address, 16)
    except ValueError as exc:
        raise ValueError("Invalid EVM address") from exc

    return "0x" + address.rjust(64, "0")


def validate_address(address: str) -> str:
    if not address:
        raise ValueError("Destination address is required")

    address = address.strip()

    if not address.startswith("0x") or len(address) != 42:
        raise ValueError("Invalid destination address")

    try:
        int(address[2:], 16)
    except ValueError as exc:
        raise ValueError("Invalid destination address") from exc

    return address


def fetch_withdrawal_transfer(
    burn_tx_hash: str,
):
    """
    Look up the Hyperliquid -> Arc CCTP transfer
    through Circle Iris.

    The Hyperliquid withdrawal transaction hash is used
    to locate the CCTP transfer once Circle indexes it.
    """

    if not burn_tx_hash:
        raise ValueError("Withdrawal transaction hash is required")

    url = (
        f"{CCTP_IRIS_API}"
        f"/v2/messages/{HYPERLIQUID_CCTP_DOMAIN}"
        f"?transactionHash={burn_tx_hash}"
    )

    response = requests.get(
        url,
        timeout=15,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    body = response.json()

    if isinstance(body, list):
        return body[0] if body else None

    if isinstance(body, dict):
        messages = body.get("messages")

        if messages:
            return messages[0]

        if body.get("status"):
            return body

    return None


def withdrawal_status(
    burn_tx_hash: str,
):
    """
    Return the simplified status consumed by the frontend.
    """

    transfer = fetch_withdrawal_transfer(
        burn_tx_hash,
    )

    if transfer is None:
        return {
            "status": "pending",
            "complete": False,
            "txHash": burn_tx_hash,
        }

    status = str(
        transfer.get("status", "")
    ).lower()

    if not status:
        status = "pending"

    return {
        "status": status,
        "complete": status == "complete",
        "txHash": burn_tx_hash,
        "messageHash": transfer.get("messageHash"),
        "forwardState": transfer.get("forwardState"),
        "forwardTxHash": transfer.get("forwardTxHash"),
    }


def withdrawal_parameters(
    amount: str,
    destination: str,
):
    """
    Return the backend configuration needed by the frontend
    to prepare a Hyperliquid -> Arc withdrawal.

    `destination` is the user's Arc wallet.

    No Arbitrum wallet is requested from the user.
    """

    destination = validate_address(destination)

    try:
        numeric_amount = float(amount)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Invalid withdrawal amount"
        ) from exc

    if numeric_amount <= 0:
        raise ValueError(
            "Withdrawal amount must be greater than zero"
        )

    # Circle's destination-domain configuration.
    #
    # Hyperliquid is the source.
    # Arc is the destination.
    #
    # The actual Hyperliquid withdraw3 call remains in
    # frontend/lib/hyperliquid.js.

    arc_recipient = address_to_bytes32(
        destination
    )

    return {
        "amount": str(amount),
        "destination": destination,
        "destinationDomain": ARC_CCTP_DOMAIN,
        "sourceDomain": HYPERLIQUID_CCTP_DOMAIN,
        "mintRecipient": arc_recipient,
        "burnToken": require(
            "HYPERLIQUID_USDC_ADDRESS"
        ),
        "arcUsdcAddress": require(
            "ARC_USDC_ADDRESS"
        ),
    }
