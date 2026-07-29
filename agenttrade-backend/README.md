# AgentTrade Backend — skeleton

Architecture: Arc = user-facing chain (wallet, deposits, dashboard).
Hyperliquid = execution backend (where trades actually happen).
Circle's CCTP bridges USDC between them.

## Where this goes

This whole folder is one deployable backend service. Structure:

```
agenttrade-backend/
├── main.py            # FastAPI app — all routes live here
├── config.py           # reads .env
├── db.py                # sqlite persistence (users, trades, bridge transfers)
├── crypto_utils.py       # encrypts delegated agent keys at rest
├── hl_client.py          # Hyperliquid: agent wallets, trades, account reads
├── bridge.py              # CCTP: Arc -> HyperEVM
├── requirements.txt
└── .env.example           # copy to .env and fill in
```

Run it anywhere that can host a long-lived Python process — free options:
Render, Railway, or Fly.io all have free tiers that work fine for this.
Locally, for testing:

```bash
cd agenttrade-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in the values below
uvicorn main:app --reload
```

## Before it actually runs, fill in .env

1. **ARC_RPC_URL / ARC_CHAIN_ID / ARC_USDC_ADDRESS** — from Arc's current
   developer docs (arc.io). These are testnet-stage and can shift, so
   pull live values rather than reusing old ones.
2. **CCTP_TOKEN_MESSENGER_ARC / CCTP_MESSAGE_TRANSMITTER_HL /
   HYPERLIQUID_CCTP_DOMAIN** — from developers.circle.com/cctp, the
   "EVM smart contracts" and "supported domains" pages.
3. **HL_API_URL** — leave on testnet
   (`https://api.hyperliquid-testnet.xyz`) until you're ready for real money.
4. **ENCRYPTION_KEY** — generate once:
   `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

## What's real vs. what's stubbed

**Real and functional:**
- Delegated Hyperliquid agent wallet generation + encrypted storage
- Trade execution routing to Hyperliquid
- Dashboard reads (positions, margin, account value)
- CCTP burn/attest/mint sequence, using Circle's actual V2 contract interface

**Deliberately not built (do these next, in order):**
- **Auth (Google/X login from your doc)** — don't hand-roll this. Drop
  in Clerk or NextAuth (both free tier) in front of this API. Not worth
  custom code.
- **`approve_agent` signing** — this has to happen in the user's wallet
  in the browser (MetaMask popup, etc), not on your backend. The backend
  only generates the address for them to approve; wire the actual
  signature request into your frontend with the Hyperliquid Python/JS SDK.
- **`/bridge/deposit` takes a raw private key over the API — fix this
  before any real funds touch it.** It's there so you can see the full
  CCTP flow end to end while testing. In production, the burn
  transaction needs to be signed client-side (user's wallet), and only
  the signed tx or resulting tx hash should reach your backend.

## Test order

1. Get Arc testnet + Hyperliquid testnet RPC/contract values into `.env`
2. `GET /markets` → confirm it returns the live Hyperliquid universe (no wallet needed for this one)
3. `POST /wallet/link` with a testnet Arc address → get back an agent address
4. Approve that agent address manually via Hyperliquid's testnet UI/SDK
5. `POST /bridge/deposit` with testnet USDC → confirm funds show up on Hyperliquid testnet
6. `POST /agents/{arc_address}/trade` → confirm a position opens
7. `GET /dashboard/{arc_address}` → confirm it reflects the position
8. `POST /agents/{arc_address}/close` → confirm the position closes

No hard limits are enforced anywhere in this backend on purpose — size,
leverage, entries, exits are 100% the agent's call, per your call to
keep it fully autonomous.
