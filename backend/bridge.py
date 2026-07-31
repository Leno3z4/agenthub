"""
CCTP bridge: Arc (source) -> HyperEVM (destination), so a user's Arc
balance can fund trades that execute on Hyperliquid.

Flow (Circle's standard CCTP V2 flow, 3 steps):
  1. burn — happens in the user's OWN wallet, client-side in the
     frontend (wagmi/viem + a wallet popup, same pattern as
     approve_agent). The backend never sees a private key for this —
     it only ever receives the resulting public tx hash.
  2. fetch_attestation() — poll Circle's free Iris API for the signed proof
  3. mint_on_hyperevm()  — submit that proof to HyperEVM's MessageTransmitterV2,
     signed by the PLATFORM's own relayer key, not the user's. This is
     safe because CCTP's destinationCaller is left at zero (see the
     frontend's depositForBurn call) — anyone can complete a mint once
     the burn is attested, by design.

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
    """Submits the attested burn to HyperEVM. relayer_private_key is
    the PLATFORM's own operational key (from config.RELAYER_PRIVATE_KEY),
    never a user's — this works because the frontend's depositForBurn
    call leaves destinationCaller at zero, meaning any funded key can
    complete the mint once Circle has attested it. Fund this key with
    a small amount of native gas on HyperEVM; it never touches user funds."""
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
