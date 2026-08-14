from __future__ import annotations

import os


ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "5042"))
ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://rpc.arc.network")

ARC_USDC = os.getenv(
    "ARC_USDC",
    "0x3600000000000000000000000000000000000000",
)

ARC_UNIVERSAL_ROUTER = os.getenv(
    "ARC_UNIVERSAL_ROUTER",
    "0x4fca4a51ab4f23a7447b3284fbd7d73289a89fb1",
)

# Fill this from the exact Arc deployment before enabling v4 pool reads.
ARC_UNISWAP_STATE_VIEW = os.getenv("ARC_UNISWAP_STATE_VIEW", "")
