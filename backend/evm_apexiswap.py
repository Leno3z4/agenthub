from __future__ import annotations
import time
from dataclasses import dataclass, asdict
from web3 import Web3
from evm_pool_discovery import checksum

FACTORY_ABI=[{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"stateMutability":"view","type":"function"}]
PAIR_ABI=[
{"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"reserve0","type":"uint112"},{"internalType":"uint112","name":"reserve1","type":"uint112"},{"internalType":"uint32","name":"blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"},
{"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
{"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
ROUTER_ABI=[
{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},
{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"}]

@dataclass(frozen=True)
class Pair:
    address:str; token0:str; token1:str; reserve0:int; reserve1:int
    def as_dict(self): return asdict(self)

@dataclass(frozen=True)
class Quote:
    amount_in:int; amount_out:int; amount_out_minimum:int; path:list[str]; router:str; pair:str
    def as_dict(self): return asdict(self)

def discover_pair(w3:Web3,factory_address:str,token_in:str,token_out:str)->Pair:
    if not factory_address: raise ValueError("APEXISWAP_FACTORY is not configured.")
    factory=w3.eth.contract(address=checksum(factory_address),abi=FACTORY_ABI)
    a,b=checksum(token_in),checksum(token_out)
    address=factory.functions.getPair(a,b).call()
    if int(address,16)==0: raise ValueError("No Apexiswap pair exists for this token pair.")
    address=checksum(address)
    pair=w3.eth.contract(address=address,abi=PAIR_ABI)
    t0,t1=checksum(pair.functions.token0().call()),checksum(pair.functions.token1().call())
    r0,r1,_=pair.functions.getReserves().call()
    if r0==0 or r1==0: raise ValueError("Apexiswap pair has zero liquidity.")
    return Pair(address,t0,t1,r0,r1)

def quote(w3:Web3,router_address:str,pair:Pair,token_in:str,token_out:str,amount_in:int,slippage_bps:int)->Quote:
    if not router_address: raise ValueError("APEXISWAP_ROUTER is not configured.")
    if amount_in<=0: raise ValueError("amount_in must be positive.")
    if not 0<=slippage_bps<=5000: raise ValueError("invalid slippage_bps.")
    router=w3.eth.contract(address=checksum(router_address),abi=ROUTER_ABI)
    path=[checksum(token_in),checksum(token_out)]
    amount_out=router.functions.getAmountsOut(amount_in,path).call()[-1]
    if amount_out<=0: raise ValueError("Apexiswap returned zero output.")
    minimum=amount_out*(10000-slippage_bps)//10000
    return Quote(amount_in,amount_out,minimum,path,checksum(router_address),pair.address)

def build_swap(w3:Web3,router_address:str,wallet_address:str,token_in:str,token_out:str,amount_in:int,amount_out_minimum:int,deadline_seconds:int=60)->dict:
    if amount_in<=0 or amount_out_minimum<=0: raise ValueError("Invalid swap amounts.")
    wallet=checksum(wallet_address)
    router=w3.eth.contract(address=checksum(router_address),abi=ROUTER_ABI)
    return router.functions.swapExactTokensForTokens(
        amount_in,amount_out_minimum,[checksum(token_in),checksum(token_out)],wallet,int(time.time())+deadline_seconds
    ).build_transaction({"from":wallet,"chainId":w3.eth.chain_id,"nonce":w3.eth.get_transaction_count(wallet,"pending"),"value":0})
