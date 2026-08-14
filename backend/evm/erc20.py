from web3 import Web3
from .rpc import checksum_address

ERC20_ABI=[
 {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
 {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
 {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
 {"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
 {"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
]

def contract(w3: Web3, token_address: str):
    return w3.eth.contract(address=checksum_address(w3, token_address), abi=ERC20_ABI)

def decimals(w3, token_address): return contract(w3, token_address).functions.decimals().call()
def symbol(w3, token_address): return contract(w3, token_address).functions.symbol().call()
def balance(w3, token_address, owner): return contract(w3, token_address).functions.balanceOf(checksum_address(w3, owner)).call()
def allowance(w3, token_address, owner, spender): return contract(w3, token_address).functions.allowance(checksum_address(w3, owner), checksum_address(w3, spender)).call()

def build_approval(w3, token_address, owner, spender, amount):
    if amount < 0: raise ValueError("Approval amount cannot be negative.")
    owner=checksum_address(w3, owner)
    return contract(w3, token_address).functions.approve(checksum_address(w3, spender), amount).build_transaction({
        "from": owner, "chainId": w3.eth.chain_id,
        "nonce": w3.eth.get_transaction_count(owner, "pending"), "value": 0,
    })

