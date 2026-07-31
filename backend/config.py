import os
from dotenv import load_dotenv

load_dotenv()

# ---------- Arc ----------

ARC_RPC_URL = os.getenv("ARC_RPC_URL", "")
ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "0"))
ARC_USDC_ADDRESS = os.getenv("ARC_USDC_ADDRESS", "")

# ---------- Circle CCTP ----------

CCTP_TOKEN_MESSENGER_ARC = os.getenv(
    "CCTP_TOKEN_MESSENGER_ARC",
    "",
)

CCTP_IRIS_API = os.getenv(
    "CCTP_IRIS_API",
    "https://iris-api-sandbox.circle.com",
)

HYPERLIQUID_CCTP_DOMAIN = int(
    os.getenv(
        "HYPERLIQUID_CCTP_DOMAIN",
        "0",
    )
)

# ---------- HyperCore ----------

CCTP_FORWARDER = os.getenv(
    "CCTP_FORWARDER",
    "",
)

CORE_DEPOSIT_WALLET = os.getenv(
    "CORE_DEPOSIT_WALLET",
    "",
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

CCTP_TOKEN_MESSENGER_ARC = require(
    CCTP_TOKEN_MESSENGER_ARC,
    "CCTP_TOKEN_MESSENGER_ARC",
)

CCTP_FORWARDER = require(
    CCTP_FORWARDER,
    "CCTP_FORWARDER",
)

CORE_DEPOSIT_WALLET = require(
    CORE_DEPOSIT_WALLET,
    "CORE_DEPOSIT_WALLET",
)

ENCRYPTION_KEY = require(
    ENCRYPTION_KEY,
    "ENCRYPTION_KEY",
)
