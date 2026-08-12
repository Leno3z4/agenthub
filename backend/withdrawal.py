"""Alias withdrawal orchestration: HyperCore -> Arbitrum -> CCTP -> Arc."""

from __future__ import annotations

import time
import uuid
from typing import Any

from hl_client import get_account_state
from bridge import start_cctp_arc_transfer


def get_withdrawable_amount(user_address: str) -> float:
    state = get_account_state(user_address)
    perp = float(state.get("withdrawable", 0) or 0)
    spot = float(state.get("spot_usdc_available", 0) or 0)
    return max(0.0, perp, spot)


def create_withdrawal(
    *,
    user_address: str,
    amount: str,
    arc_destination: str,
) -> dict[str, Any]:
    if not user_address:
        raise ValueError("Hyperliquid account address is required.")
    if not arc_destination:
        raise ValueError("Arc destination wallet is required.")

    value = float(amount)
    if value <= 0:
        raise ValueError("Withdrawal amount must be greater than zero.")

    available = get_withdrawable_amount(user_address)
    if value > available:
        raise ValueError(
            f"Withdrawal exceeds available balance. Maximum: {available:.6f} USDC."
        )

    withdrawal_id = str(uuid.uuid4())

    # The bridge layer is responsible for the Hyperliquid -> Arbitrum receiver
    # and then Arbitrum -> Arc through CCTP. Never send withdraw3 directly to Arc.
    bridge_job = start_cctp_arc_transfer(
        withdrawal_id=withdrawal_id,
        amount=str(value),
        arc_destination=arc_destination,
    )

    return {
        "withdrawal_id": withdrawal_id,
        "status": bridge_job.get("status", "pending"),
        "amount": str(value),
        "destination": arc_destination,
        "route": "hypercore->arbitrum->cctp->arc",
        "created_at": int(time.time() * 1000),
    }
