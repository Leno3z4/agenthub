from __future__ import annotations
import os
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from web3 import Web3
from evm_config import ARC_RPC_URL,DEFAULT_SLIPPAGE_BPS
from evm_apexiswap import discover_pair,quote,build_swap

router=APIRouter(prefix="/evm/apexiswap",tags=["evm-apexiswap"])
APEXISWAP_FACTORY=os.getenv("APEXISWAP_FACTORY","")
APEXISWAP_ROUTER=os.getenv("APEXISWAP_ROUTER","")

class PairRequest(BaseModel):
    token_in:str
    token_out:str
class QuoteRequest(BaseModel):
    token_in:str; token_out:str; amount_in:int=Field(gt=0); slippage_bps:int=Field(default=DEFAULT_SLIPPAGE_BPS,ge=0,le=5000)
class SwapBuildRequest(BaseModel):
    wallet_address:str; token_in:str; token_out:str; amount_in:int=Field(gt=0); amount_out_minimum:int=Field(gt=0); deadline_seconds:int=Field(default=60,ge=15,le=300)

def _w3():
    w3=Web3(Web3.HTTPProvider(ARC_RPC_URL,request_kwargs={"timeout":15}))
    if not w3.is_connected(): raise RuntimeError("Unable to connect to Arc RPC.")
    return w3

def _json_tx(tx):
    return {k:("0x"+v.hex() if isinstance(v,bytes) else str(v) if isinstance(v,int) else v) for k,v in tx.items()}

@router.post("/pair")
def pair(req:PairRequest):
    try:
        w3=_w3(); p=discover_pair(w3,APEXISWAP_FACTORY,req.token_in,req.token_out)
        return {"chain_id":w3.eth.chain_id,"pair":p.as_dict()}
    except Exception as e: raise HTTPException(400,str(e))

@router.post("/quote")
def apex_quote(req:QuoteRequest):
    try:
        w3=_w3(); p=discover_pair(w3,APEXISWAP_FACTORY,req.token_in,req.token_out)
        q=quote(w3,APEXISWAP_ROUTER,p,req.token_in,req.token_out,req.amount_in,req.slippage_bps)
        return {"chain_id":w3.eth.chain_id,"quote":q.as_dict()}
    except Exception as e: raise HTTPException(400,str(e))

@router.post("/swap/build")
def swap_build(req:SwapBuildRequest):
    try:
        w3=_w3(); tx=build_swap(w3,APEXISWAP_ROUTER,req.wallet_address,req.token_in,req.token_out,req.amount_in,req.amount_out_minimum,req.deadline_seconds)
        w3.eth.call(tx); tx["gas"]=w3.eth.estimate_gas(tx)
        return {"chain_id":w3.eth.chain_id,"simulation":"passed","transaction":_json_tx(tx)}
    except Exception as e: raise HTTPException(400,str(e))
