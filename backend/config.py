import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

print("ENV KEY:", os.getenv("ENCRYPTION_KEY"))
print("CWD:", os.getcwd())
# ---------- Arc ----------

ARC_RPC_URL = os.getenv("ARC_RPC_URL", "")
ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "0"))
ARC_USDC_ADDRESS = os.getenv("ARC_USDC_ADDRESS", "")

# ---------- Authentication ----------

# This is the OAuth client ID accepted by the backend. It is never taken from
# a request body, profile object, or other frontend-provided field.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()

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
ARC_CCTP_DOMAIN = int(
        os.getenv(
            "ARC_CCTP_DOMAIN",
            "7",   # confirmed Arc testnet CCTP domain
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

SESSION_REDIS_URL = os.getenv(
    "SESSION_REDIS_URL",
    "redis://localhost:6379/0",
)
SESSION_TTL_SECONDS = int(
    os.getenv(
        "SESSION_TTL_SECONDS",
        str(30 * 24 * 60 * 60),
    )
)

ENCRYPTION_KEY = os.getenv(
    "ENCRYPTION_KEY",
    "",
)

# ---------- CORS ----------

ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

if not ALLOWED_ORIGINS:
    logger.warning(
        "ALLOWED_ORIGINS is empty; cross-origin browser requests are disabled."
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
