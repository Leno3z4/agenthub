from __future__ import annotations

import os

ARC_TESTNET_CHAIN_ID = 5042002
ARC_MAINNET_CHAIN_ID = 5042

ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", str(ARC_TESTNET_CHAIN_ID)))
ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://rpc.testnet.arc.network")

# Arc's native USDC ERC-20 interface.
ARC_USDC = os.getenv(
    "ARC_USDC",
    "0x3600000000000000000000000000000000000000",
)

# Keep protocol deployments configurable. Do not assume a mainnet address
# exists on Arc Testnet.
UNISWAP_V3_FACTORY = os.getenv("UNISWAP_V3_FACTORY", "")
UNISWAP_V3_QUOTER_V2 = os.getenv("UNISWAP_V3_QUOTER_V2", "")
UNISWAP_V3_SWAP_ROUTER = os.getenv("UNISWAP_V3_SWAP_ROUTER", "")

# Optional testnet DEX deployment if you choose to use one for a live test.
TESTNET_DEX_FACTORY = os.getenv("TESTNET_DEX_FACTORY", "")
TESTNET_DEX_QUOTER = os.getenv("TESTNET_DEX_QUOTER", "")
TESTNET_DEX_ROUTER = os.getenv("TESTNET_DEX_ROUTER", "")

DEFAULT_FEE_TIERS = (100, 500, 3000, 10000)
DEFAULT_SLIPPAGE_BPS = 100
DEFAULT_DEADLINE_SECONDS = 60
