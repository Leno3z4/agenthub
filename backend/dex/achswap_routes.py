from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config import ARC_RPC_URL
from evm.rpc import get_web3
from dex.achswap import quote

from pydantic import BaseModel
from fastapi import HTTPException
from evm.rpc import get_web3
from dex.achswap import quote as achswap_quote, build_swap


router = APIRouter(prefix="/evm/achswap", tags=["AchSwap"])


class QuoteRequest(BaseModel):
    token_in: str
    token_out: str
    amount_in: int = Field(gt=0)
    slippage_bps: int = Field(default=100, ge=0, le=10_000)


@router.post("/quote")
def achswap_quote(body: QuoteRequest):
    try:
        w3 = get_web3(ARC_RPC_URL, expected_chain_id=5042002)
        q = quote(w3, body.token_in, body.token_out, body.amount_in, body.slippage_bps)
        return {
            "chain_id": 5042002,
            "token_in": q.token_in,
            "token_out": q.token_out,
            "amount_in": q.amount_in,
            "expected_out": q.expected_out,
            "minimum_out": q.minimum_out,
            "route_data": q.route_data,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    
class AchSwapSwapRequest(BaseModel):
    token_in: str
    token_out: str
    amount_in: int
    slippage_bps: int = 100
    sender: str


@router.post("/swap")
def build_achswap_swap(req: AchSwapSwapRequest):
    try:
        w3 = get_web3(expected_chain_id=5042002)

        q = achswap_quote(
            w3,
            req.token_in,
            req.token_out,
            req.amount_in,
            req.slippage_bps,
        )

        tx = build_swap(
            w3,
            req.sender,
            q,
        )

        return {
            "chainId": tx["chainId"],
            "to": tx["to"],
            "data": tx["data"],
            "value": str(tx.get("value", 0)),
            "nonce": tx["nonce"],
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        print("ACHSWAP SWAP BUILD ERROR:", repr(exc))
        raise HTTPException(
            status_code=502,
            detail="Unable to build AchSwap swap transaction.",
        )
