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
5. **RELAYER_PRIVATE_KEY** — a fresh, dedicated key that only ever pays
   gas to complete CCTP mints. Generate with:
   `python -c "from eth_account import Account; a = Account.create(); print(a.key.hex())"`
   Fund its address with a small amount of native gas on HyperEVM.
   It never has access to any user's funds — see `bridge.py` for why
   that's safe (destinationCaller is left at zero).

## What's real vs. what's stubbed

**Real and functional:**
- Delegated Hyperliquid agent wallet generation + encrypted storage
- API key auth on every fund-moving endpoint (`/trade`, `/close`,
  `/bridge/deposit`, `/wallet/confirm-permissions`) — issued once at
  `/wallet/link`, required as `Authorization: Bearer <key>` from then on
- Re-linking an already-approved wallet is blocked (`409`), so a
  stranger can't hijack or brick a live setup by re-calling `/wallet/link`
- Trade execution routing to Hyperliquid, with optional agent-reported
  reasoning/confidence/model/strategy for real dashboard monitoring
- `/agents/{address}/status` — connection state, approval state, latest
  action — auth-gated, since reasoning/strategy text is proprietary
- Dashboard reads (positions, margin, account value)
- CCTP attest/mint sequence, using Circle's actual V2 contract interface
  and a platform-owned relayer key — **no private key of any kind ever
  reaches this backend**, user or otherwise

**Deliberately not built (do these next, in order):**
- **Auth (Google/X login from your doc)** — don't hand-roll this. Drop
  in Clerk or NextAuth (both free tier) in front of this API. Not worth
  custom code.
- **`approve_agent` signing** — this has to happen in the user's wallet
  in the browser (MetaMask popup, etc), not on your backend. The backend
  only generates the address for them to approve; wire the actual
  signature request into your frontend with the Hyperliquid Python/JS SDK.
- **The CCTP burn signature** — same deal. `/bridge/deposit` now takes
  a `burn_tx_hash`, not a private key — the frontend needs to have the
  user's own wallet sign and submit the `depositForBurn` call directly
  (wagmi/viem), then hand the resulting hash to this endpoint. That
  frontend piece isn't built yet.

## Test order

1. Get Arc testnet + Hyperliquid testnet RPC/contract values into `.env`,
   plus a funded `RELAYER_PRIVATE_KEY`
2. `GET /skill` → confirm it returns the skill doc with `{base_url}` replaced by your real URL
3. `GET /markets` → confirm it returns the live Hyperliquid universe (no wallet needed for this one)
4. `POST /wallet/link` with a testnet Arc address → get back an agent address **and an api_key** — save both
5. Approve that agent address manually via Hyperliquid's testnet UI/SDK
6. `POST /wallet/confirm-permissions` with `Authorization: Bearer <api_key>` → confirm `{"confirmed": true}`
7. Try `POST /agents/{arc_address}/trade` **without** the Authorization header → confirm you get a `401`
8. Same call **with** `Authorization: Bearer <api_key>` → confirm a position opens
9. `GET /agents/{arc_address}/status` with the key → confirm it shows the trade you just made
10. `GET /dashboard/{arc_address}` → confirm it reflects the position
11. `POST /agents/{arc_address}/close` (with auth) → confirm the position closes
12. Try `POST /wallet/link` again for the *same* address → confirm you get a `409`, not a silent overwrite

No hard limits are enforced anywhere in this backend on purpose — size,
leverage, entries, exits are 100% the agent's call, per your call to
keep it fully autonomous. That's separate from auth: auth controls
*who* can act, not *what* they're allowed to do once verified.

## The /skill endpoint

This is the actual "connect an agent" mechanism — same pattern as
dev.fun Arena. A user pastes `{your_url}/skill` into their coding
agent's chat (Claude Code, Cursor, etc). The agent reads it, walks
the human through the one-time wallet approval, then operates the
rest of the API (`/markets`, `/agents/{address}/trade`,
`/agents/{address}/close`) entirely on its own from then on.

Edit `ALIAS_SKILL.md` directly to change what agents are told — it's
plain markdown, served as-is with `{base_url}` swapped for your real
deployed URL.
