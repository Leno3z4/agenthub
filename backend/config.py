import os
from dotenv import load_dotenv

load_dotenv()

print("CWD:", os.getcwd())


# ---------------------------------------------------------------------
# Arc
# ---------------------------------------------------------------------

ARC_RPC_URL = os.getenv(
    "ARC_RPC_URL",
    "https://rpc.testnet.arc.io",
)

ARC_CHAIN_ID = int(
    os.getenv("ARC_CHAIN_ID", "5042002")
)

ARC_USDC_ADDRESS = os.getenv(
    "ARC_USDC_ADDRESS",
    "0x3600000000000000000000000000000000000000",
)


def require(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}"
        )

    return value


# ---------------------------------------------------------------------
# Circle CCTP
# ---------------------------------------------------------------------

CCTP_IRIS_API = require("CCTP_IRIS_API")

CCTP_TOKEN_MESSENGER_ARC = os.getenv(
    "CCTP_TOKEN_MESSENGER_ARC",
    "0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA",
)

ARC_CCTP_DOMAIN = int(
    require("ARC_CCTP_DOMAIN")
)

HYPERLIQUID_CCTP_DOMAIN = int(
    require("HYPERLIQUID_CCTP_DOMAIN")
)

CCTP_FORWARDER = os.getenv(
    "CCTP_FORWARDER",
    "0x02e39ECb8368b41bF68FF99ff351aC9864e5E2a2",
)


# ---------------------------------------------------------------------
# HyperCore
# ---------------------------------------------------------------------

CORE_DEPOSIT_WALLET = os.getenv(
    "CORE_DEPOSIT_WALLET",
    "0x0B80659a4076E9E93C7DbE0f10675A16a3e5C206",
)

HL_API_URL = os.getenv(
    "HL_API_URL",
    "https://api.hyperliquid-testnet.xyz",
)


# ---------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------

DB_PATH = os.getenv(
    "DB_PATH",
    "agenttrade.db",
)

ENCRYPTION_KEY = require("ENCRYPTION_KEY")



ARBITRUM_RPC_URL = os.getenv(
    "ARBITRUM_RPC_URL",
    "https://sepolia-rollup.arbitrum.io/rpc",
)

ARBITRUM_CHAIN_ID = int(
    os.getenv("ARBITRUM_CHAIN_ID", "421614")
)

ARBITRUM_CCTP_DOMAIN = int(
    os.getenv("ARBITRUM_CCTP_DOMAIN", "3")
)

ARBITRUM_USDC_ADDRESS = os.getenv(
    "ARBITRUM_USDC_ADDRESS",
    "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d",
)

ARBITRUM_TOKEN_MESSENGER = os.getenv(
    "ARBITRUM_TOKEN_MESSENGER",
    "0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA",
)

HL_WITHDRAW_RECEIVER_ADDRESS = require(
    "HL_WITHDRAW_RECEIVER_ADDRESS"
)

WITHDRAW_RELAYER_PRIVATE_KEY = require(
    "WITHDRAW_RELAYER_PRIVATE_KEY"
)
