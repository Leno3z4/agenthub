from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class EvmToken:
    address: str
    decimals: int
    symbol: str | None = None

@dataclass(frozen=True)
class EvmTransaction:
    to: str
    data: str
    value: int = 0
    chain_id: int | None = None
    nonce: int | None = None
    gas: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in {
            "to": self.to, "data": self.data, "value": self.value,
            "chainId": self.chain_id, "nonce": self.nonce, "gas": self.gas,
        }.items() if v is not None}

