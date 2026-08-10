export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "https://agenthub-g0m8.onrender.com";

export async function registerUser(data) {
  const res = await fetch(`${BACKEND_URL}/users/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(text);
  return JSON.parse(text);
}

export async function linkWallet({ user_id, google_id, email, name, picture, wallet_address }) {
  const res = await fetch(`${BACKEND_URL}/wallet/link`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, google_id, email, name, picture, wallet_address }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function confirmPermissions(userId, apiKey) {
  const res = await fetch(`${BACKEND_URL}/wallet/confirm-permissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
export async function repairAgent(userId, apiKey) {
  const res = await fetch(
    `${BACKEND_URL}/agent/repair?user_id=${encodeURIComponent(userId)}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
    }
  );

  const data = await res.json();

  if (!res.ok) {
    throw new Error(
      data.detail || "Failed to repair agent"
    );
  }

  return data;
}
export async function depositParams(amount, hypercoreRecipient) {
  const res = await fetch(`${BACKEND_URL}/bridge/deposit-params`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount, hypercore_recipient: hypercoreRecipient }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deposit(userId, apiKey, burnTxHash, amount) {
  const res = await fetch(`${BACKEND_URL}/bridge/deposit`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({ user_id: userId, burn_tx_hash: burnTxHash, amount_usdc_units: amount }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function bridgeStatus(burnTxHash) {
  const res = await fetch(`${BACKEND_URL}/bridge/status/${burnTxHash}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createAgent(userId, apiKey) {
  const res = await fetch(`${BACKEND_URL}/agent/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, api_key: apiKey }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAgentStatus(userId, apiKey) {
  const res = await fetch(`${BACKEND_URL}/users/${userId}/agent/status`, {
    headers: { Authorization: `Bearer ${apiKey}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAgentProfile(userId, apiKey) {
  const res = await fetch(`${BACKEND_URL}/agent/profile/${userId}?api_key=${encodeURIComponent(apiKey)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAgentHistory(userId, apiKey) {
  const res = await fetch(`${BACKEND_URL}/agent/history/${userId}?api_key=${encodeURIComponent(apiKey)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getMarkets() {
  const res = await fetch(`${BACKEND_URL}/markets`, { cache: "no-store" });
  if (!res.ok) throw new Error(`backend returned ${res.status}`);
  return res.json();
}

export async function getMarketCandles(coin, interval = "1h", hours = 48) {
  const res = await fetch(
    `${BACKEND_URL}/agent/markets/${encodeURIComponent(coin)}/candles?interval=${encodeURIComponent(interval)}&hours=${hours}`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function pctChange(market) {
  const mark = parseFloat(market.mark_price);
  const prev = parseFloat(market.prev_day_price);
  if (!prev) return 0;
  return ((mark - prev) / prev) * 100;
}

export function fmtPrice(value) {
  const n = parseFloat(value);
  if (Number.isNaN(n)) return "—";
  return n < 1 ? n.toFixed(4) : n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function fmtVolume(value) {
  const n = parseFloat(value);
  if (Number.isNaN(n)) return "—";
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toFixed(0);
}

export async function getDashboard(userId, apiKey) {
  const res = await fetch(`${BACKEND_URL}/users/${userId}/dashboard`, {
    headers: { Authorization: `Bearer ${apiKey}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}



export async function getGatewayBalance(walletAddress) {
  const res = await fetch(
    `${BACKEND_URL}/gateway/balance/${walletAddress}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}
