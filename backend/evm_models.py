from pydantic import BaseModel, Field


class EvmBalanceRequest(BaseModel):
    wallet_address: str
    token_address: str


class EvmBalanceResponse(BaseModel):
    wallet_address: str
    token_address: str
    balance_raw: str


class EvmApprovalRequest(BaseModel):
    wallet_address: str
    token_address: str
    spender: str
    amount_raw: str = Field(gt=0)


class EvmSwapBuildRequest(BaseModel):
    wallet_address: str
    commands_hex: str
    inputs_hex: list[str]
    value_raw: str = "0"


class EvmSendRequest(BaseModel):
    wallet_address: str
    raw_transaction: str
