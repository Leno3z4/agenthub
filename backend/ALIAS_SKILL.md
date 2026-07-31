# Alias — Agent Trading Skill

You are being connected to Alias, a perpetual futures execution platform.
Alias never decides trades — you do. It only executes what you tell it,
signed on your user's behalf through a delegated permission that cannot
withdraw funds. There are no platform-enforced limits on size, leverage,
entries, or exits: those decisions are entirely yours.

If you are a coding agent (Claude Code, Cursor, etc.) reading this on
behalf of a human: walk them through Step 1 interactively, since it
requires their wallet signature. Steps 2 onward you can automate and
run yourself, indefinitely, without asking again.

## Step 1 — Register (requires the human, one time only)

Call this with the user's Arc wallet address:

```
POST {base_url}/wallet/link
{ "arc_address": "0x..." }
```

This returns an `agent_address` and an `api_key`. **The `api_key` is
shown exactly once and cannot be retrieved again** — store it
securely wherever you keep your own config. Every trade or close call
you make must include it as `Authorization: Bearer <api_key>`, or the
request is rejected. Without this, anyone who knew the wallet address
could trigger trades on the user's behalf — this key is what proves
it's actually you.

Tell the human to approve the `agent_address` from their own wallet
via Hyperliquid's `approve_agent` action (this is a signature they
make themselves — you cannot do this for them, and Alias never sees
their private key). Once they confirm it's approved, you're done with
setup permanently for this user.

## Step 2 — Discover what's tradable (do this yourself, anytime)

```
GET {base_url}/markets
```

Returns every live perpetual market: coin, mark price, funding rate,
open interest, day volume, max leverage. Nothing here is curated for
you — pull it yourself and decide what looks worth trading.

## Step 3 — Check the account (do this yourself, anytime)

```
GET {base_url}/dashboard/{arc_address}
```

Returns account value, margin used, and current open positions. Check
this before and after any decision you make.

## Step 4 — Open a position (your call entirely)

```
POST {base_url}/agents/{arc_address}/trade
Authorization: Bearer <your_api_key>
{ "coin": "BTC", "is_buy": true, "size": 0.01, "leverage": 3 }
```

`is_buy: true` = long, `false` = short. Alias does not validate or cap
this — whatever you send, executes.

Optionally, report your own reasoning alongside the trade — this is
purely for the human's monitoring dashboard, it changes nothing about
execution:

```
{ ..., "reasoning": "momentum crossed threshold", "confidence": 0.92,
  "model": "claude-sonnet-5", "strategy": "momentum-v2" }
```

## Step 5 — Close a position (your call entirely)

```
POST {base_url}/agents/{arc_address}/close
Authorization: Bearer <your_api_key>
{ "coin": "BTC" }
```

Omit `size` to close the full position, or include it to close
partially. The same optional `reasoning`/`confidence`/`model`/
`strategy` fields work here too.

## Status (optional, for your own awareness)

```
GET {base_url}/agents/{arc_address}/status
```

Returns whether permissions are confirmed and the most recent action
taken — useful if you want to check your own state before acting.

## Operating loop

Steps 2–5 are yours to run however you see fit — on a timer, on a
webhook, continuously, whatever your own reasoning calls for. Alias
places no restrictions on frequency, strategy, or risk. The only human
checkpoint is Step 1, once, ever.
