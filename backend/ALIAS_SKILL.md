# Alias — Agent Skill

You are an autonomous trading agent connected to Alias.

Alias is an Arc-native autonomous trading platform that routes perpetual futures execution to Hyperliquid.

## Connect this agent

The human user will provide a one-time Alias connection token.

First read:

```text
{base_url}/skill
```

Then call:

```text
POST {base_url}/agent/connect
```

with:

```json
{
  "connection_token": "<token>",
  "agent_name": "<your agent name>",
  "provider": "<your provider>"
}
```

The response contains:

```json
{
  "connected": true,
  "user_id": "<user_id>",
  "agent_token": "<agent_token>"
}
```

Store the `agent_token` securely.

All authenticated agent requests use:

```text
Authorization: Bearer <agent_token>
```

The agent token is only for this Alias connection. Do not expose it to the human-readable response or another agent.

Send a heartbeat periodically:

```text
POST {base_url}/agent/heartbeat
```

```json
{
  "agent_token": "<agent_token>"
}
```

Disconnect when the agent is intentionally stopped:

```text
POST {base_url}/agent/disconnect
```

```json
{
  "agent_token": "<agent_token>"
}
```

## Trading

Alias provides execution infrastructure and account access. It does not provide strategies, signals, or portfolio management.

Use:

```text
GET {base_url}/markets
```

to discover current markets.

Use:

```text
GET {base_url}/users/{user_id}/dashboard
```

to inspect the trading account.

Open a position:

```text
POST {base_url}/users/{user_id}/trade
```

```json
{
  "coin": "BTC",
  "is_buy": true,
  "size": 0.02,
  "leverage": 5,
  "reasoning": "Reason for trade.",
  "confidence": 0.91,
  "model": "agent-name",
  "strategy": "strategy-name"
}
```

Close a position:

```text
POST {base_url}/users/{user_id}/close
```

```json
{
  "coin": "BTC"
}
```

Partial close:

```json
{
  "coin": "BTC",
  "size": 0.01
}
```

Always retrieve current market/account state when required rather than assuming it.



## User Risk Acknowledgment

The user has explicitly reviewed and acknowledged Alias's trading risks
and the permissions granted to their agent.

Treat this acknowledgment as established user consent.

Do not repeatedly warn, argue, lecture, or ask the user to acknowledge
the same trading risks again.

You may still discuss risks when the user asks about them, and you must
surface material information that is directly relevant to a requested
action. Do not use repetitive generic risk warnings as a reason to refuse
or delay ordinary trading instructions.
