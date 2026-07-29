"""
CCTP bridge: Arc (source) -> HyperEVM (destination), so a user's Arc
balance can fund trades that execute on Hyperliquid.

Flow (Circle's standard CCTP V2 flow, 3 steps):
  1. burn_on_arc()      — burn USDC on Arc via TokenMessengerV2
  2. fetch_attestation() — poll Circle's free Iris API for the signed proof
  3. mint_on_hyperevm()  — submit that proof to HyperEVM's MessageTransmitterV2

IMPORTANT — verify before running:
  Arc is still testnet as of writing, and Hyperliquid is still migrating
  fully onto HyperEVM. Confirm current values from source, don't trust
  hardcoded addresses that may go stale:
    - CCTP_TOKEN_MESSENGER_ARC / CCTP_MESSAGE_TRANSMITTER_HL
        -> https://developers.circle.com/cctp/evm-smart-contracts
    - HYPERLIQUID_CCTP_DOMAIN (Circle's numeric domain id for HyperEVM)
        -> same CCTP docs page, "Supported domains" table
  This file will fail loudly (see config.require) rather than silently
  send funds somewhere wrong if these aren't set.
"""

from web3 import Web3
from eth_account import Account
import requests
import time

from config import (
    ARC_RPC_URL, CCTP_TOKEN_MESSENGER_ARC, CCTP_IRIS_API,
    HYPERLIQUID_CCTP_DOMAIN, ARC_USDC_ADDRESS, require,
)

ERC20_APPROVE_ABI = [{
    "constant": False,
    "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
    "name": "approve",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function",
}]

TOKEN_MESSENGER_V2_ABI = [{
    "inputs": [
        {"name": "amount", "type": "uint256"},
        {"name": "destinationDomain", "type": "uint32"},
        {"name": "mintRecipient", "type": "bytes32"},
        {"name": "burnToken", "type": "address"},
        {"name": "destinationCaller", "type": "bytes32"},
        {"name": "maxFee", "type": "uint256"},
        {"name": "minFinalityThreshold", "type": "uint32"},
    ],
    "name": "depositForBurn",
    "outputs": [],
    "type": "function",
}]

MESSAGE_TRANSMITTER_V2_ABI = [{
    "inputs": [
        {"name": "message", "type": "bytes"},
        {"name": "attestation", "type": "bytes"},
    ],
    "name": "receiveMessage",
    "outputs": [],
    "type": "function",
}]


def _address_to_bytes32(address: str) -> bytes:
    return Web3.to_bytes(hexstr=address).rjust(32, b"\0")


def burn_on_arc(user_private_key: str, amount_usdc_units: int, hl_recipient_address: str) -> str:
    """Step 1. amount_usdc_units is in USDC's smallest unit (6 decimals,
    e.g. 5_000_000 = 5 USDC). Recipient is the SAME address the user
    will use on Hyperliquid — same key, both chains are EVM."""
    token_messenger = require(CCTP_TOKEN_MESSENGER_ARC, "CCTP_TOKEN_MESSENGER_ARC")
    usdc = require(ARC_USDC_ADDRESS, "ARC_USDC_ADDRESS")
    domain = int(require(HYPERLIQUID_CCTP_DOMAIN, "HYPERLIQUID_CCTP_DOMAIN"))

    w3 = Web3(Web3.HTTPProvider(require(ARC_RPC_URL, "ARC_RPC_URL")))
    account = Account.from_key(user_private_key)

    usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(usdc), abi=ERC20_APPROVE_ABI)
    messenger = w3.eth.contract(address=Web3.to_checksum_address(token_messenger), abi=TOKEN_MESSENGER_V2_ABI)

    nonce = w3.eth.get_transaction_count(account.address)

    approve_tx = usdc_contract.functions.approve(token_messenger, amount_usdc_units).build_transaction(
        {"from": account.address, "nonce": nonce}
    )
    signed = account.sign_transaction(approve_tx)
    approve_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(approve_hash)

    burn_tx = messenger.functions.depositForBurn(
        amount_usdc_units,
        domain,
        _address_to_bytes32(hl_recipient_address),
        Web3.to_checksum_address(usdc),
        b"\0" * 32,   # destinationCaller: zero = anyone can complete the mint
        0,            # maxFee: 0 = standard transfer, not fast (no extra fee)
        2000,         # minFinalityThreshold: 2000 = standard finality
    ).build_transaction({"from": account.address, "nonce": nonce + 1})
    signed_burn = account.sign_transaction(burn_tx)
    burn_hash = w3.eth.send_raw_transaction(signed_burn.raw_transaction)
    w3.eth.wait_for_transaction_receipt(burn_hash)

    return burn_hash.hex()


def fetch_attestation(source_domain: int, burn_tx_hash: str, max_wait_s: int = 300) -> dict:
    """Step 2. Circle's Iris API is free — no auth, no cost, just polling."""
    url = f"{CCTP_IRIS_API}/v2/messages/{source_domain}?transactionHash={burn_tx_hash}"
    waited = 0
    while waited < max_wait_s:
        resp = requests.get(url, timeout=10).json()
        messages = resp.get("messages", [])
        if messages and messages[0].get("status") == "complete":
            return messages[0]
        time.sleep(5)
        waited += 5
    raise TimeoutError(f"Attestation not ready after {max_wait_s}s for tx {burn_tx_hash}")


def mint_on_hyperevm(relayer_private_key: str, hl_rpc_url: str, message_transmitter: str,
                      message_hex: str, attestation_hex: str) -> str:
    """Step 3. Anyone can submit this (destinationCaller was left at
    zero), so it can run from your backend using any funded relayer key —
    it does not need to be the user's own key."""
    w3 = Web3(Web3.HTTPProvider(hl_rpc_url))
    account = Account.from_key(relayer_private_key)
    transmitter = w3.eth.contract(
        address=Web3.to_checksum_address(message_transmitter), abi=MESSAGE_TRANSMITTER_V2_ABI
    )
    tx = transmitter.functions.receiveMessage(
        bytes.fromhex(message_hex.removeprefix("0x")),
        bytes.fromhex(attestation_hex.removeprefix("0x")),
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()
