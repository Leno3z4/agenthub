import os 
from dotenv import load_dotenv

load_dotenv()
print("CWD:", os.getcwd())
# ---------- Arc ----------

ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://rpc.testnet.arc.io")
ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "5042002"))
ARC_USDC_ADDRESS = os.getenv("ARC_USDC_ADDRESS", "0x3600000000000000000000000000000000000000")

# ---------- Circle CCTP ----------

CCTP_TOKEN_MESSENGER_ARC = os.getenv(
    "CCTP_TOKEN_MESSENGER_ARC",
    "0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA",
)

CCTP_IRIS_API = os.getenv(
    "CCTP_IRIS_API",
    "https://iris-api-sandbox.circle.com",
)

HYPERLIQUID_CCTP_DOMAIN = int(
    os.getenv(
        "HYPERLIQUID_CCTP_DOMAIN",
        "19",
    )
)
ARC_CCTP_DOMAIN = int(
        os.getenv(
            "ARC_CCTP_DOMAIN",
            "26",   # confirmed Arc testnet CCTP domain
        )
)
# ---------- HyperCore ----------

CCTP_FORWARDER = os.getenv(
    "CCTP_FORWARDER",
    "0x02e39ECb8368b41bF68FF99ff351aC9864e5E2a2",
)

CORE_DEPOSIT_WALLET = os.getenv(
    "CORE_DEPOSIT_WALLET",
    "0x0B80659a4076E9E93C7DbE0f10675A16a3e5C206",
)

HL_API_URL = os.getenv(
    "HL_API_URL",
    "https://api.hyperliquid-testnet.xyz",
)

# ---------- Storage ----------

DB_PATH = os.getenv(
    "DB_PATH",
    "agenttrade.db",
)

ENCRYPTION_KEY = os.getenv(
    "ENCRYPTION_KEY",
    "",
)


def require(value, name):
    if value in ("", None, 0):
        raise RuntimeError(
            f"{name} is not configured."
        )
    return value


# ---------- Validate required configuration ----------

#CCTP_TOKEN_MESSENGER_ARC = require(
#    CCTP_TOKEN_MESSENGER_ARC,
#    "CCTP_TOKEN_MESSENGER_ARC",
#)

#CCTP_FORWARDER = require(
#    CCTP_FORWARDER,
#    "CCTP_FORWARDER",
#)

#CORE_DEPOSIT_WALLET = require(
#    CORE_DEPOSIT_WALLET,
#    "CORE_DEPOSIT_WALLET",
#)

ENCRYPTION_KEY = require(
    ENCRYPTION_KEY,
    "ENCRYPTION_KEY",
)
