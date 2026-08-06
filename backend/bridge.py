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
    ARC_CCTP_DOMAIN,
    ARC_USDC_ADDRESS,
    CORE_DEPOSIT_WALLET,
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
    Fetch a CCTP transfer from Circle Iris.

    Returns:
        - dict representing the transfer if found
        - None if Circle hasn't indexed it yet
    """

    url = (
        f"{CCTP_IRIS_API}"
        f"/v2/messages/{source_domain}"
        f"?transactionHash={burn_tx_hash}"
    )

    response = requests.get(url, timeout=15)

    # Circle hasn't indexed it yet.
    if response.status_code == 404:
        print("IRIS: transfer not found yet")
        return None

    response.raise_for_status()

    body = response.json()

    print("=" * 80)
    print("IRIS STATUS:", response.status_code)
    import json
    
    print(
        "IRIS RESPONSE:",
        json.dumps(body, indent=2)
    )
    print(body)
    print("=" * 80)
    print(url)

    # Iris may return either a list or an object depending on endpoint/version.

    if isinstance(body, list):
        if not body:
            return None

        return body[0]

    if isinstance(body, dict):
        # Most common format
        if "messages" in body:
            messages = body.get("messages") or []

            if not messages:
                return None

            return messages[0]

        # Already a transfer object
        if "status" in body:
            return body

    raise RuntimeError(
        f"Unexpected Iris response: {body}"
    )

# ---------------------------------------------------------------------
# Wait
# ---------------------------------------------------------------------

def fetch_max_fee(source_domain: int):
    """
    Fetches the recommended forward fee from Circle.
    """

    url = (
        f"{CCTP_IRIS_API}"
        f"/v2/burn/USDC/fees/"
        f"{source_domain}/"
        f"{HYPERLIQUID_CCTP_DOMAIN}"
        f"?forward=true"
        f"&hyperCoreDeposit=true"
    )

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    body = response.json()

    if not isinstance(body, list) or not body:
        raise RuntimeError("Unexpected Circle fee response.")

    fee_info = next(
        (
            item
            for item in body
            if item["finalityThreshold"] == 1000
        ),
        body[0],
    )
    print("Circle fee response:")
    print(body)
    
    print("Selected fee:")
    print(fee_info)
    print("High fee:", fee_info["forwardFee"]["high"])
    return int(float(fee_info["forwardFee"]["high"]) * 1_000_000)

    
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
    depositForBurnWithHook().
    """

    mint_recipient = address_to_bytes32(
        require(
            CORE_DEPOSIT_WALLET,
            "CORE_DEPOSIT_WALLET",
        )
    )

    burn_token = require(
        ARC_USDC_ADDRESS,
        "ARC_USDC_ADDRESS",
    )

    forwarder = address_to_bytes32(
        require(
            CCTP_FORWARDER,
            "CCTP_FORWARDER",
        )
    )

    hook_data = b""

    fee = fetch_max_fee(
        ARC_CCTP_DOMAIN,
    )

    print("========== CCTP ==========")
    print("AMOUNT:", amount)
    print("MAX FEE:", fee)
    print("==========================")


    return {
        "amount": amount,
        "destinationDomain": ARC_CCTP_DOMAIN,
        "mintRecipient": mint_recipient,
        "burnToken": burn_token,
        "destinationCaller": forwarder,
        "maxFee": fee,
        "minFinalityThreshold": 1000,
        "hookData": hook_data.hex(),
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
