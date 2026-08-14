from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from web3 import Web3

from evm_config import (
    ARC_RPC_URL,
    DEFAULT_DEADLINE_SECONDS,
    DEFAULT_FEE_TIERS,
    DEFAULT_SLIPPAGE_BPS,
    UNISWAP_V3_FACTORY,
    UNISWAP_V3_QUOTER_V2,
    UNISWAP_V3_SWAP_ROUTER,
)
from evm_pool_discovery import discover_v3_pools, choose_deepest_pool
from evm_quote import quote_exact_input_single
from evm_simulation import estimate_gas, simulate_transaction
from evm_swap import build_approval, build_exact_input_single, get_allowance


router = APIRouter(prefix="/evm", tags=["evm"])


class PoolRequest(BaseModel):
    token_in: str
    token_out: str
    fees: list[int] = Field(default_factory=lambda: list(DEFAULT_FEE_TIERS))


class QuoteRequest(BaseModel):
    token_in: str
    token_out: str
    amount_in: int = Field(gt=0)
    fee: int
    slippage_bps: int = Field(default=DEFAULT_SLIPPAGE_BPS, ge=0, le=5000)


class SwapBuildRequest(BaseModel):
    wallet_address: str
    token_in: str
    token_out: str
    amount_in: int = Field(gt=0)
    amount_out_minimum: int = Field(gt=0)
    fee: int
    deadline_seconds: int = Field(
        default=DEFAULT_DEADLINE_SECONDS,
        ge=15,
        le=300,
    )


class ApprovalRequest(BaseModel):
    wallet_address: str
    token_address: str
    amount: int = Field(gt=0)


def _w3() -> Web3:
    w3 = Web3(Web3.HTTPProvider(ARC_RPC_URL, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        raise RuntimeError("Unable to connect to configured Arc RPC.")
    return w3


@router.post("/pools")
def find_pools(request: PoolRequest):
    try:
        w3 = _w3()
        pools = discover_v3_pools(
            w3,
            UNISWAP_V3_FACTORY,
            request.token_in,
            request.token_out,
            tuple(request.fees),
        )
        best = choose_deepest_pool(pools)

        return {
            "chain_id": w3.eth.chain_id,
            "pools": [pool.as_dict() for pool in pools],
            "best_pool": best.as_dict() if best else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/quote")
def quote(request: QuoteRequest):
    try:
        w3 = _w3()
        result = quote_exact_input_single(
            w3,
            UNISWAP_V3_QUOTER_V2,
            request.token_in,
            request.token_out,
            request.amount_in,
            request.fee,
            request.slippage_bps,
        )
        return result.as_dict()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/approval/build")
def approval(request: ApprovalRequest):
    try:
        w3 = _w3()
        allowance = get_allowance(
            w3,
            request.token_address,
            request.wallet_address,
            UNISWAP_V3_SWAP_ROUTER,
        )

        if allowance >= request.amount:
            return {
                "required": False,
                "allowance": str(allowance),
            }

        tx = build_approval(
            w3,
            request.token_address,
            request.wallet_address,
            UNISWAP_V3_SWAP_ROUTER,
            request.amount,
        )

        tx["gas"] = estimate_gas(w3, tx)

        return {
            "required": True,
            "allowance": str(allowance),
            "transaction": _json_tx(tx),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/swap/build")
def swap_build(request: SwapBuildRequest):
    try:
        w3 = _w3()

        tx = build_exact_input_single(
            w3,
            UNISWAP_V3_SWAP_ROUTER,
            request.token_in,
            request.token_out,
            request.fee,
            request.wallet_address,
            request.amount_in,
            request.amount_out_minimum,
            request.deadline_seconds,
        )

        # Simulate before returning a transaction for signing.
        simulate_transaction(w3, tx)
        tx["gas"] = estimate_gas(w3, tx)

        return {
            "chain_id": w3.eth.chain_id,
            "simulation": "passed",
            "transaction": _json_tx(tx),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _json_tx(tx: dict) -> dict:
    result = {}
    for key, value in tx.items():
        if isinstance(value, bytes):
            result[key] = "0x" + value.hex()
        elif isinstance(value, int):
            result[key] = str(value)
        else:
            result[key] = value
    return result
