from web3 import Web3
from config import ARC_CHAIN_ID, ARC_RPC_URL

def get_web3(rpc_url: str = ARC_RPC_URL, expected_chain_id: int | None = ARC_CHAIN_ID) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        raise RuntimeError(f"Unable to connect to EVM RPC: {rpc_url}")
    if expected_chain_id is not None and w3.eth.chain_id != expected_chain_id:
        raise RuntimeError(f"Unexpected chain ID: {w3.eth.chain_id}; expected {expected_chain_id}")
    return w3

def checksum_address(w3: Web3, address: str) -> str:
    try:
        return w3.to_checksum_address(address)
    except ValueError as exc:
        raise ValueError(f"Invalid EVM address: {address}") from exc

def native_balance(w3: Web3, address: str) -> int:
    return w3.eth.get_balance(checksum_address(w3, address))

