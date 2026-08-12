"""
HyperCore -> HyperEVM -> CCTP -> Arc withdrawal support.

The actual withdrawal is user-signed in the frontend with Hyperliquid's
sendToEvmWithData action.

Hyperliquid routes the Core withdrawal through HyperEVM. HyperEVM then
uses CCTP to burn USDC, and CCTP Forwarding Service automatically mints
the USDC to the user's Arc Testnet wallet when data="0x".
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import requests

from config import (
    ARC_CCTP_DOMAIN,
    CCTP_IRIS_API,
    HYPERLIQUID_CCTP_DOMAIN,
)
from hl_client import get_account_state


USDC_DECIMALS = 6
HL_WITHDRAWAL_FEE = 1.0

# Hyperliquid's sendToEvmWithData uses an empty data field to request
# automatic CCTP forwarding. The frontend sends "0x".
AUTOMATIC_FORWARDING_DATA = "0x"

ROUTE = "hypercore->hyperevm->cctp->arc"


def _address(value: str) -> str:
    value = (value or "").strip()

    if not value.startswith("0x") or len(value) != 42:
        raise ValueError(f"Invalid EVM address: {value!r}")

    try:
        int(value[2:], 16)
    except ValueError:
        raise ValueError(f"Invalid EVM address: {value!r}")

    return value


def _get_forwarding_fee_quote() -> dict[str, Any]:
    """
    Fetch the current CCTP forwarding quote immediately before withdrawal.

    HyperEVM is CCTP domain 19 and Arc Testnet is domain 26.
    """
    url = (
        f"{CCTP_IRIS_API.rstrip('/')}/v2/burn/USDC/fees/"
        f"{HYPERLIQUID_CCTP_DOMAIN}/{ARC_CCTP_DOMAIN}"
        "?forward=true"
    )

    response = requests.get(
        url,
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    response.raise_for_status()

    body = response.json()

    if not isinstance(body, list) or not body:
        raise RuntimeError(
            "Circle returned an unexpected forwarding-fee response."
        )

    selected = next(
        (
            item
            for item in body
            if item.get("finalityThreshold") == 1000
        ),
        body[0],
    )

    forward_fee = selected.get("forwardFee") or {}

    # Circle's API returns fee values in USDC base units.
    # Prefer the medium quote, then high, then low.
    fee_units = (
        forward_fee.get("med")
        or forward_fee.get("high")
        or forward_fee.get("low")
    )

    if fee_units is None:
        raise RuntimeError(
            "Circle forwarding-fee response did not contain a forward fee."
        )

    minimum_fee = selected.get("minimumFee", 0)

    return {
        "finality_threshold": selected.get(
            "finalityThreshold",
            1000,
        ),
        "forward_fee_units": int(fee_units),
        "minimum_fee": float(minimum_fee or 0),
    }


def get_forwarding_fee() -> float:
    quote = _get_forwarding_fee_quote()
    return quote["forward_fee_units"] / 10**USDC_DECIMALS


def _select_withdrawal_source(
    user_address: str,
) -> tuple[str, str, float]:
    """
    Return:
      source label,
      Hyperliquid sourceDex value,
      available USDC.

    sourceDex="" means perp.
    sourceDex="spot" means Spot.
    """
    state = get_account_state(user_address)

    perp_available = max(
        0.0,
        float(state.get("perp_withdrawable", 0) or 0),
    )

    spot_available = max(
        0.0,
        float(state.get("spot_usdc_available", 0) or 0),
    )

    if perp_available >= spot_available and perp_available > 0:
        return "perp", "", perp_available

    if spot_available > 0:
        return "spot", "spot", spot_available

    raise ValueError("No USDC is currently withdrawable from Hyperliquid.")


def withdrawal_parameters(
    *,
    user_address: str,
    amount: str,
    destination: str,
) -> dict[str, Any]:
    destination = _address(destination)

    requested = float(amount)

    if requested <= 0:
        raise ValueError("Withdrawal amount must be greater than zero.")

    source, source_dex, available = _select_withdrawal_source(
        user_address
    )

    quote = _get_forwarding_fee_quote()

    forward_fee = (
        quote["forward_fee_units"] / 10**USDC_DECIMALS
    )

    # The amount requested by the user is the amount intended for the
    # Arc wallet. The forwarding fee is added to the HyperCore amount.
    hyperliquid_amount = requested + forward_fee

    total_hypercore_debit = (
        hyperliquid_amount + HL_WITHDRAWAL_FEE
    )

    maximum_receivable = max(
        0.0,
        available - HL_WITHDRAWAL_FEE - forward_fee,
    )

    if requested > maximum_receivable:
        raise ValueError(
            f"Maximum withdrawable amount is "
            f"${maximum_receivable:.2f} after the "
            f"${HL_WITHDRAWAL_FEE:.2f} Hyperliquid withdrawal fee "
            f"and ${forward_fee:.6f} CCTP forwarding fee."
        )

    return {
        "destination": destination,
        "amount": f"{requested:.6f}",
        "hyperliquid_amount": f"{hyperliquid_amount:.6f}",
        "source": source,
        "source_dex": source_dex,
        "available": f"{available:.6f}",
        "maximum_receivable": f"{maximum_receivable:.6f}",
        "hyperliquid_fee": HL_WITHDRAWAL_FEE,
        "cctp_forward_fee": forward_fee,
        "total_hypercore_debit": f"{total_hypercore_debit:.6f}",
        "route": ROUTE,
        "data": AUTOMATIC_FORWARDING_DATA,
        "destination_chain_id": ARC_CCTP_DOMAIN,
    }


def get_withdrawable_amount(user_address: str) -> float:
    state = get_account_state(user_address)

    return max(
        0.0,
        float(state.get("withdrawable_total", 0) or 0),
    )


def create_withdrawal(
    *,
    user_address: str,
    amount: str,
    arc_destination: str,
) -> dict[str, Any]:
    params = withdrawal_parameters(
        user_address=user_address,
        amount=amount,
        destination=arc_destination,
    )

    return {
        "withdrawal_id": str(uuid.uuid4()),
        "status": "awaiting_user_signature",
        **params,
    }


def process_withdrawal(
    *,
    withdrawal_id: str,
    hyperliquid_amount: str,
    arc_destination: str,
    source_dex: str = "",
    hyperliquid_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Record the fact that the user-signed Hyperliquid action was accepted.

    No backend private key is used and no Arbitrum transaction is created.
    """
    destination = _address(arc_destination)

    return {
        "withdrawal_id": withdrawal_id,
        "status": "submitted",
        "amount": hyperliquid_amount,
        "destination": destination,
        "source_dex": source_dex,
        "hyperliquid_result": hyperliquid_result,
        "route": ROUTE,
    }


def withdrawal_status(burn_tx_hash: str) -> dict[str, Any]:
    """
    Compatibility endpoint for old callers.

    New withdrawals are initiated by Hyperliquid's sendToEvmWithData
    action, so there is no Arbitrum burn transaction to poll here.
    """
    return {
        "status": "submitted",
        "complete": False,
        "hyperliquid_tx": burn_tx_hash,
        "route": ROUTE,
    }
