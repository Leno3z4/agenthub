import os
from dotenv import load_dotenv

load_dotenv()

# --- Arc (user-facing chain) ---
ARC_RPC_URL = os.getenv("ARC_RPC_URL", "")
ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "0"))
ARC_USDC_ADDRESS = os.getenv("ARC_USDC_ADDRESS", "")

# --- CCTP bridge: Arc -> HyperEVM ---
CCTP_TOKEN_MESSENGER_ARC = os.getenv("CCTP_TOKEN_MESSENGER_ARC", "")
CCTP_MESSAGE_TRANSMITTER_HL = os.getenv("CCTP_MESSAGE_TRANSMITTER_HL", "")
CCTP_IRIS_API = os.getenv("CCTP_IRIS_API", "https://iris-api-sandbox.circle.com")
HYPERLIQUID_CCTP_DOMAIN = os.getenv("HYPERLIQUID_CCTP_DOMAIN", "")

# --- Hyperliquid ---
HL_API_URL = os.getenv("HL_API_URL", "https://api.hyperliquid-testnet.xyz")

# --- Storage / security ---
DB_PATH = os.getenv("DB_PATH", "agenttrade.db")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")


def require(value: str, name: str) -> str:
    """Fail loudly instead of silently trading with an empty/placeholder value."""
    if not value:
        raise RuntimeError(f"{name} is not set — fill it in your .env before running this.")
    return value
