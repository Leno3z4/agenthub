"""HyperCore -> Arbitrum -> CCTP Forwarding Service -> Arc withdrawals."""

from __future__ import annotations

import time
import uuid
from typing import Any

import requests
from eth_account import Account
from web3 import Web3

from config import (
    ARBITRUM_CCTP_DOMAIN,
    ARBITRUM_RPC_URL,
    ARBITRUM_TOKEN_MESSENGER,
    ARBITRUM_USDC_ADDRESS,
    ARC_CCTP_DOMAIN,
    CCTP_IRIS_API,
    HL_WITHDRAW_RECEIVER_ADDRESS,
    WITHDRAW_RELAYER_PRIVATE_KEY,
)
from hl_client import get_account_state

USDC_DECIMALS = 6
HL_WITHDRAWAL_FEE = 1.0
FORWARD_HOOK_DATA = (
    "0x636374702d666f72776172640000000000000000000000000000000000000000"
)

ERC20_ABI = [
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "approve",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "name": "allowance",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "outputs": [{"name": "", "type": "uint256"}],
    },
]

TOKEN_MESSENGER_ABI = [
    {
        "name": "depositForBurnWithHook",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "amount", "type": "uint256"},
            {"name": "destinationDomain", "type": "uint32"},
            {"name": "mintRecipient", "type": "bytes32"},
            {"name": "burnToken", "type": "address"},
            {"name": "destinationCaller", "type": "bytes32"},
            {"name": "maxFee", "type": "uint256"},
            {"name": "minFinalityThreshold", "type": "uint32"},
            {"name": "hookData", "type": "bytes"},
        ],
        "outputs": [],
    },
]


def _address(value: str) -> str:
    if not Web3.is_address(value):
        raise ValueError(f"Invalid EVM address: {value!r}")
    return Web3.to_checksum_address(value)


def _bytes32_address(value: str) -> bytes:
    return bytes.fromhex(_address(value)[2:].rjust(64, "0"))


def _arbitrum() -> tuple[Web3, Any]:
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC_URL, request_kwargs={"timeout": 20}))
    if not w3.is_connected():
        raise RuntimeError("Arbitrum RPC is unavailable.")
    account = Account.from_key(WITHDRAW_RELAYER_PRIVATE_KEY)
    return w3, account


def get_forwarding_fee() -> int:
    url = (
        f"{CCTP_IRIS_API.rstrip('/')}/v2/burn/USDC/fees/"
        f"{ARBITRUM_CCTP_DOMAIN}/{ARC_CCTP_DOMAIN}"
        "?forward=true"
    )
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    body = response.json()

    if not isinstance(body, list) or not body:
        raise RuntimeError("Unexpected Circle forwarding-fee response.")

    selected = next(
        (item for item in body if item.get("finalityThreshold") == 1000),
        body[0],
    )
    forward_fee = selected.get("forwardFee", {}).get("high")
    if forward_fee is None:
        raise RuntimeError("Circle response does not contain forwardFee.")

    return int(forward_fee)


def withdrawal_parameters(
    *,
    amount: str,
    destination: str,
) -> dict[str, Any]:
    destination = _address(destination)
    requested = float(amount)

    if requested <= 0:
        raise ValueError("Withdrawal amount must be greater than zero.")

    fee_units = get_forwarding_fee()
    cctp_fee = fee_units / 10**USDC_DECIMALS

    # The user chooses the amount they want to receive on Arc.
    # CCTP forwarding fee is taken from the source amount, so withdraw
    # requested amount + CCTP fee from HyperCore. Hyperliquid charges
    # its separate $1 withdrawal fee.
    hyperliquid_amount = requested + cctp_fee

    return {
        "destination": destination,
        "relay_destination": _address(HL_WITHDRAW_RECEIVER_ADDRESS),
        "amount": f"{requested:.6f}",
        "hyperliquid_amount": f"{hyperliquid_amount:.6f}",
        "hyperliquid_fee": HL_WITHDRAWAL_FEE,
        "cctp_forward_fee": cctp_fee,
        "total_hypercore_debit": f"{hyperliquid_amount + HL_WITHDRAWAL_FEE:.6f}",
        "route": "hypercore->arbitrum->cctp->arc",
    }


def get_withdrawable_amount(user_address: str) -> float:
    state = get_account_state(user_address)
    return max(
        0.0,
        float(state.get("withdrawable_total", 0) or 0),
    )


def _wait_for_relay_balance(
    w3: Web3,
    relay: str,
    minimum_units: int,
    timeout: int = 420,
) -> int:
    token = w3.eth.contract(
        address=_address(ARBITRUM_USDC_ADDRESS),
        abi=ERC20_ABI,
    )
    started = time.time()

    while time.time() - started < timeout:
        balance = int(token.functions.balanceOf(_address(relay)).call())
        if balance >= minimum_units:
            return balance
        time.sleep(5)

    raise TimeoutError("Timed out waiting for Hyperliquid withdrawal on Arbitrum.")


def _send_cctp_burn(
    w3: Web3,
    account: Any,
    amount_units: int,
    destination: str,
    max_fee_units: int,
) -> str:
    token_address = _address(ARBITRUM_USDC_ADDRESS)
    messenger_address = _address(ARBITRUM_TOKEN_MESSENGER)

    token = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    messenger = w3.eth.contract(
        address=messenger_address,
        abi=TOKEN_MESSENGER_ABI,
    )

    allowance = int(
        token.functions.allowance(account.address, messenger_address).call()
    )

    nonce = w3.eth.get_transaction_count(account.address)
    if allowance < amount_units:
        approve_tx = token.functions.approve(
            messenger_address,
            amount_units,
        ).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "chainId": 421614,
                "gas": 120000,
                "gasPrice": w3.eth.gas_price,
            }
        )
        signed = account.sign_transaction(approve_tx)
        approve_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(approve_hash)
        nonce += 1

    burn_tx = messenger.functions.depositForBurnWithHook(
        amount_units,
        26,
        _bytes32_address(destination),
        token_address,
        bytes(32),
        max_fee_units,
        1000,
        bytes.fromhex(FORWARD_HOOK_DATA[2:]),
    ).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": 421614,
            "gas": 500000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    signed = account.sign_transaction(burn_tx)
    burn_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(burn_hash)

    if receipt.status != 1:
        raise RuntimeError("Arbitrum CCTP burn transaction failed.")

    return burn_hash.hex()


def _wait_for_forward(
    burn_tx_hash: str,
    timeout: int = 600,
) -> dict[str, Any]:
    url = (
        f"{CCTP_IRIS_API.rstrip('/')}/v2/messages/"
        f"{ARBITRUM_CCTP_DOMAIN}"
        f"?transactionHash={burn_tx_hash}"
    )
    started = time.time()

    while time.time() - started < timeout:
        response = requests.get(url, timeout=15)

        if response.ok:
            body = response.json()
            messages = body.get("messages") or []

            if messages:
                message = messages[0]
                if message.get("forwardTxHash"):
                    return message
                if message.get("status") == "failed":
                    raise RuntimeError("Circle marked the CCTP transfer as failed.")

        time.sleep(5)

    raise TimeoutError("Timed out waiting for Circle to forward USDC to Arc.")


def create_withdrawal(
    *,
    user_address: str,
    amount: str,
    arc_destination: str,
) -> dict[str, Any]:
    params = withdrawal_parameters(
        amount=amount,
        destination=arc_destination,
    )

    requested = float(params["amount"])
    available = get_withdrawable_amount(user_address)
    total_debit = float(params["total_hypercore_debit"])

    if total_debit > available:
        raise ValueError(
            f"Maximum withdrawable after fees is "
            f"${max(0.0, available - HL_WITHDRAWAL_FEE - float(params['cctp_forward_fee'])):.2f}."
        )

    return {
        "withdrawal_id": str(uuid.uuid4()),
        "status": "awaiting_hyperliquid_withdrawal",
        "amount": f"{requested:.6f}",
        "hyperliquid_amount": params["hyperliquid_amount"],
        "relay_destination": params["relay_destination"],
        "destination": params["destination"],
        "cctp_forward_fee": params["cctp_forward_fee"],
        "hyperliquid_fee": HL_WITHDRAWAL_FEE,
        "route": "hypercore->arbitrum->cctp->arc",
    }


def process_withdrawal(
    *,
    withdrawal_id: str,
    hyperliquid_amount: str,
    arc_destination: str,
) -> dict[str, Any]:
    w3, account = _arbitrum()

    amount_units = round(float(hyperliquid_amount) * 10**USDC_DECIMALS)
    fee_units = get_forwarding_fee()

    _wait_for_relay_balance(
        w3,
        account.address,
        amount_units,
    )

    burn_tx_hash = _send_cctp_burn(
        w3,
        account,
        amount_units,
        arc_destination,
        fee_units,
    )

    message = _wait_for_forward(burn_tx_hash)

    return {
        "withdrawal_id": withdrawal_id,
        "status": "complete",
        "amount": hyperliquid_amount,
        "destination": arc_destination,
        "burn_tx_hash": burn_tx_hash,
        "forward_tx_hash": message["forwardTxHash"],
        "route": "hypercore->arbitrum->cctp->arc",
    }


def withdrawal_status(burn_tx_hash: str) -> dict[str, Any]:
    url = (
        f"{CCTP_IRIS_API.rstrip('/')}/v2/messages/"
        f"{ARBITRUM_CCTP_DOMAIN}"
        f"?transactionHash={burn_tx_hash}"
    )
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    body = response.json()
    message = (body.get("messages") or [None])[0]

    if not message:
        return {"status": "pending", "complete": False}

    return {
        "status": message.get("status", "pending"),
        "complete": bool(message.get("forwardTxHash")),
        "burn_tx_hash": burn_tx_hash,
        "forward_tx_hash": message.get("forwardTxHash"),
    }
