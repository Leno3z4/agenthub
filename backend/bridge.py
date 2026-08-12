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
from typing import Any
from config import (
    CCTP_IRIS_API,
    HYPERLIQUID_CCTP_DOMAIN,
    CCTP_FORWARDER,
    ARC_CCTP_DOMAIN,
    CCTP_TOKEN_MESSENGER_ARC,
    require,
)




def address_to_bytes32(address: str) -> str:
    address = address.removeprefix("0x")

    if len(address) != 40:
        raise ValueError(
            f"Invalid EVM address: {address}"
        )

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
    Fetch the current CCTP fee for a HyperCore deposit.

    Circle's API returns forwardFee values in USDC
    micro-units/subunits.

    Example:
        238902 = 0.238902 USDC
    """

    url = (
        f"{CCTP_IRIS_API}"
        f"/v2/burn/USDC/fees/"
        f"{source_domain}/"
        f"{HYPERLIQUID_CCTP_DOMAIN}"
        f"?forward=true"
        f"&hyperCoreDeposit=true"
    )

    response = requests.get(
        url,
        timeout=15,
    )

    response.raise_for_status()

    body = response.json()

    print("Circle fee response:")
    print(body)

    if not isinstance(body, list) or not body:
        raise RuntimeError(
            "Unexpected Circle fee response."
        )

    fee_info = next(
        (
            item
            for item in body
            if item.get("finalityThreshold") == 1000
        ),
        body[0],
    )

    print("Selected fee:")
    print(fee_info)

    forward_fee = fee_info.get("forwardFee")

    if not forward_fee:
        raise RuntimeError(
            "Circle response does not contain forwardFee."
        )

    high_fee = int(
        forward_fee["high"]
    )

    print("High fee:", high_fee)

    return int(
        fee_info["forwardFee"]["high"]
    )

    
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
    hypercore_recipient: str,
    destination_dex: int = 0,
) -> str:
    """
    Circle HyperCore CctpForwarder hook format:

        bytes 0-23   magicBytes
        bytes 24-27  version
        bytes 28-31  dataLength
        bytes 32-51  hyperCoreMintRecipient
        bytes 52-55  destinationDex

    destination_dex:
        0          = Perps
        0xffffffff = Spot
    """

    recipient = hypercore_recipient.removeprefix("0x")

    if len(recipient) != 40:
        raise ValueError(
            "hypercore_recipient must be a 20-byte EVM address"
        )

    if not 0 <= destination_dex <= 0xFFFFFFFF:
        raise ValueError(
            "destination_dex must fit uint32"
        )

    # "cctp-forward" padded to 24 bytes.
    magic = (
        "cctp-forward"
        .encode("utf-8")
        .hex()
        .ljust(48, "0")
    )

    # uint32(0)
    version = "00000000"

    # Recipient = 20 bytes + destinationDex = 4 bytes
    # Total payload = 24 bytes.
    data_length = "00000018"

    recipient_hex = recipient.lower()

    dex_hex = destination_dex.to_bytes(
        4,
        "big",
    ).hex()

    return (
        "0x"
        + magic
        + version
        + data_length
        + recipient_hex
        + dex_hex
    )




# ---------------------------------------------------------------------
# Frontend deposit parameters
# ---------------------------------------------------------------------


def deposit_parameters(
    amount: int,
    hypercore_recipient: str,
):
    """
    Returns everything the frontend needs for
    depositForBurnWithHook().
    """

    if amount <= 0:
        raise ValueError(
            "Amount must be greater than zero."
        )

    if not hypercore_recipient:
        raise ValueError(
            "HyperCore recipient is required."
        )

    forwarder = address_to_bytes32(
        require(
            "CCTP_FORWARDER",
        )
    )

    # Hook recipient is the user's HyperCore/EVM address.
    hook_data = create_hook_data(
        hypercore_recipient,
        destination_dex=0,
    )

    fee = fetch_max_fee(
        ARC_CCTP_DOMAIN,
    )

    # Circle requires the CctpForwarder as both:
    # mintRecipient and destinationCaller.
    mint_recipient = forwarder
    destination_caller = forwarder

    # USDC contract on Arc.
    burn_token = require(
        "ARC_USDC_ADDRESS",
    )

    print("========== CCTP ==========")
    print("AMOUNT:", amount)
    print("MAX FEE:", fee)
    print("DESTINATION DOMAIN:", HYPERLIQUID_CCTP_DOMAIN)
    print("MINT RECIPIENT:", mint_recipient)
    print("DESTINATION CALLER:", destination_caller)
    print("BURN TOKEN:", burn_token)
    print("HYPERCORE RECIPIENT:", hypercore_recipient)
    print("HOOK DATA:", hook_data)
    print("==========================")

    return {
        "amount": amount,
        "destinationDomain": HYPERLIQUID_CCTP_DOMAIN,
        "mintRecipient": mint_recipient,
        "burnToken": burn_token,
        "destinationCaller": destination_caller,
        "maxFee": fee,
        "minFinalityThreshold": 1000,
        "hookData": hook_data,
    }
    

# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------


def validate_transfer(transfer: dict):
    if not transfer:
        return False

    status = transfer.get("status")

    if not status:
        print("IRIS VALIDATION FAILED: missing status")
        return False

    message_hash = transfer.get("messageHash")

    if not message_hash:
        print("IRIS VALIDATION FAILED: missing messageHash")
        print("IRIS TRANSFER KEYS:", list(transfer.keys()))
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

    status = str(transfer.get("status", "")).lower()

    if not status:
        print("IRIS RESPONSE HAS NO STATUS")
        print("TRANSFER:", transfer)

        return {
            "status": "pending",
            "complete": False,
        }

    return {
        "status": status,
        "complete": status == "complete",
        "messageHash": transfer.get("messageHash"),
        "txHash": burn_tx_hash,
        "forwardState": transfer.get("forwardState"),
        "forwardTxHash": transfer.get("forwardTxHash"),
    }

def start_cctp_arc_transfer(
    *,
    withdrawal_id: str,
    amount: str,
    arc_destination: str,
) -> dict[str, Any]:
    if not arc_destination.startswith("0x") or len(arc_destination) != 42:
        raise ValueError("Invalid Arc destination address.")

    if not amount or float(amount) <= 0:
        raise ValueError("Invalid transfer amount.")

    if not CCTP_IRIS_API:
        raise RuntimeError("CCTP Iris API is not configured.")

    if ARC_CCTP_DOMAIN is None:
        raise RuntimeError("Arc CCTP domain is not configured.")

    # IMPORTANT:
    # Wire this call to the EXISTING CCTP burn/attestation/mint implementation
    # already present in the repository. Do not duplicate that implementation.
    return {
        "withdrawal_id": withdrawal_id,
        "status": "pending",
        "amount": amount,
        "destination": arc_destination,
        "destination_domain": ARC_CCTP_DOMAIN,
        "token_messenger_arc": CCTP_TOKEN_MESSENGER_ARC,
    }
