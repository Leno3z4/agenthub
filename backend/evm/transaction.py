from typing import Any
from web3 import Web3

def simulate(w3: Web3, tx: dict[str, Any]) -> None:
    w3.eth.call(tx)

def estimate_gas(w3: Web3, tx: dict[str, Any]) -> int:
    return w3.eth.estimate_gas(tx)

def prepare_transaction(w3: Web3, *, from_address: str, to: str, data: str, value: int = 0) -> dict[str, Any]:
    sender=w3.to_checksum_address(from_address)
    tx={"from":sender,"to":w3.to_checksum_address(to),"data":data,"value":value,
        "chainId":w3.eth.chain_id,"nonce":w3.eth.get_transaction_count(sender,"pending")}
    simulate(w3, tx)
    tx["gas"]=estimate_gas(w3, tx)
    return tx

def serialize_transaction(tx: dict[str, Any]) -> dict[str, Any]:
    return {k:("0x"+v.hex() if isinstance(v,bytes) else str(v) if isinstance(v,int) else v) for k,v in tx.items()}

