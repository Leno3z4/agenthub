"""
FastAPI routes for read-only quote/discovery operations.

Execution endpoints should be added only after transaction simulation and
Universal Router calldata encoding are pinned and tested.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from evm_client import get_web3
from evm_pool_discovery import discover_v3_pools, choose_deepest_v3_pool
from evm_quote import quote_exact_input_single


router = APIRouter(prefix="/evm", tags=["evm"])


class PoolDiscoveryRequest(BaseModel):
    factory_address: str
    token_in: str
    token_out: str
    fees: list[int] = Field(default_factory=lambda: [100, 500, 3000, 10000])


class QuoteRequest(BaseModel):
    quoter_address: str
    token_in: str
    token_out: str
    amount_in: int = Field(gt=0)
    fee: int
    slippage_bps: int = Field(default=100, ge=0, le=5000)


@router.post("/pools")
def pools(request: PoolDiscoveryRequest):
    try:
        w3 = get_web3()
        result = discover_v3_pools(
            w3,
            request.factory_address,
            request.token_in,
            request.token_out,
            tuple(request.fees),
        )
        return {
            "pools": [pool.__dict__ for pool in result],
            "best_pool": (
                choose_deepest_v3_pool(result).__dict__
                if result else None
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/quote")
def quote(request: QuoteRequest):
    try:
        w3 = get_web3()
        result = quote_exact_input_single(
            w3,
            request.quoter_address,
            request.token_in,
            request.token_out,
            request.amount_in,
            request.fee,
            request.slippage_bps,
        )
        return result.__dict__
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
