"""
Official Circle CCTP -> HyperCore bridge helpers.

Flow

Frontend
    |
depositForBurn()
    |
    v
Arc
    |
    v
Circle CCTP
    |
    v
CctpForwarder
    |
    v
CoreDepositWallet
    |
    v
HyperCore

Backend responsibilities:

• Build hookData
• Poll Circle Iris
• Report transfer status
• Never custody user funds
"""

import time
import requests

from config import (
    CCTP_IRIS_API,
    HYPERLIQUID_CCTP_DOMAIN,
    CCTP_FORWARDER,
    require,
)





def address_to_bytes32(address: str) -> str:
    address = address.removeprefix("0x")
    return "0x" + address.rjust(64, "0")

# ---------------------------------------------------------------------
# Circle
# ---------------------------------------------------------------------


def fetch_transfer(source_domain: int, burn_tx_hash: str):
    """
    Returns Circle's transfer object.
    """

    url = (
        f"{CCTP_IRIS_API}"
        f"/v2/messages/{source_domain}"
        f"?transactionHash={burn_tx_hash}"
    )

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    body = response.json()

    messages = body.get("messages", [])

    if not messages:
        return None

    return messages[0]


# ---------------------------------------------------------------------
# Wait
# ---------------------------------------------------------------------


def wait_for_completion(
    source_domain: int,
    burn_tx_hash: str,
    timeout: int = 300,
    poll_interval: int = 5,
):
    """
    Polls Circle Iris until the bridge completes.
    """

    waited = 0

    while waited < timeout:

        transfer = fetch_transfer(
            source_domain,
            burn_tx_hash,
        )

        if transfer:

            status = transfer.get("status", "").lower()

            if status == "complete":
                return transfer

            if status == "failed":
                raise RuntimeError(
                    "Circle marked transfer as failed."
                )

        time.sleep(poll_interval)
        waited += poll_interval

    raise TimeoutError(
        "Timed out waiting for Circle."
    )


# ---------------------------------------------------------------------
# HyperCore hook data
# ---------------------------------------------------------------------


FORWARDER_PREFIX = b"cctp-forward"

PROTOCOL_VERSION = bytes([1])


def create_hook_data(
    destination_dex: int = 0,
):
    """
    Builds the hookData consumed by Hyperliquid's
    CctpForwarder.

    destination_dex

    0              -> Perps

    0xffffffff     -> Spot
    """

    return (
        FORWARDER_PREFIX
        + PROTOCOL_VERSION
        + destination_dex.to_bytes(4, "big")
    )


# ---------------------------------------------------------------------
# Frontend deposit parameters
# ---------------------------------------------------------------------


def deposit_parameters(amount: int):
    """
    Returns everything the frontend needs for
    depositForBurn().
    """

    return {
        "amount": amount,
        "destinationDomain": HYPERLIQUID_CCTP_DOMAIN,
        "mintRecipient": address_to_bytes32(
            require(
                CCTP_FORWARDER,
                "CCTP_FORWARDER",
            ),
        ),
        "hookData": "0x" + create_hook_data().hex(),
    }


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------


def validate_transfer(transfer: dict):

    if not transfer:
        return False

    required = [
        "status",
        "messageHash",
    ]

    for field in required:
        if field not in transfer:
            return False

    return True


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------


def bridge_status(
    source_domain: int,
    burn_tx_hash: str,
):
    """
    Returns a simplified transfer status
    for the frontend.
    """

    transfer = fetch_transfer(
        source_domain,
        burn_tx_hash,
    )

    if transfer is None:
        return {
            "status": "pending",
            "complete": False,
        }

    if not validate_transfer(transfer):
        return {
            "status": "invalid",
            "complete": False,
        }

    status = transfer["status"]

    return {
        "status": status,
        "complete": status.lower() == "complete",
        "messageHash": transfer["messageHash"],
        "txHash": burn_tx_hash,
    }
