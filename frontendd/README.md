# Alias — frontend structure

Next.js (App Router), plain JS, Tailwind. Matches the site map below.
(Renamed from AgentTrade — internal folder/package name is unchanged,
only user-facing text was updated. Rename the folder yourself if you want it to match.)

## Pages built

```
/                       landing page — video hero (public/videos/hero-bg.mp4),
                         only this page has the video background
/onboarding             5-step setup wizard (sign in -> connect wallet ->
                         authorize -> connect agent -> fund wallet)
/dashboard               overview: balances, P&L, open positions
/dashboard/markets        live token list, pulled from the backend's
                           GET /markets — which itself pulls straight
                           from Hyperliquid. No mock data left here.
/dashboard/markets/[coin]  price, funding, OI, volume for one market,
                            plus a copyable setup snippet for wiring
                            an agent's tool definitions (direction is
                            deliberately left out — that's the agent's
                            call, always)
/dashboard/agent          API endpoint the user's AI agent calls
/dashboard/history         trade history
/dashboard/settings         network toggle, revoke access
```

This mirrors the User Journey section of the project plan 1:1 — each
doc step maps to either an onboarding step or a dashboard page.

## Run it locally

```bash
npm install
cp .env.local.example .env.local   # point at your backend, defaults to localhost:8000
npm run dev
```

Opens on http://localhost:3000. For `/dashboard/markets` to show real
data, the backend needs to be running too (`uvicorn main:app --reload`
in the backend repo) — otherwise you'll see a clear "couldn't reach
backend" message instead of a crash.

## Deploy (when ready)

Push to GitHub, then import the repo on Vercel (free Hobby tier, no
card). Every push auto-deploys. Set `NEXT_PUBLIC_BACKEND_URL` in
Vercel's project settings to wherever the backend ends up (Oracle,
Render, etc) once that's live.

## What's next (in order)

1. Wire real wallet connect (wagmi/viem) into `/onboarding`
2. Wire the `approve_agent` signature request (talks to the backend's
   `/wallet/link` endpoint from the backend repo)
3. Replace dashboard overview placeholders with real reads from the
   backend's `/dashboard/{address}` endpoint
4. Auth (Google/X) — drop in Clerk or NextAuth in front of everything
