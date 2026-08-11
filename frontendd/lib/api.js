export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "https://agenthub-g0m8.onrender.com";

/*
 * One-time cleanup for older Alias builds that stored the backend
 * credential in localStorage. New code never writes it there.
 */
if (typeof window !== "undefined") {
  localStorage.removeItem("alias_api_key");
}

async function privateFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.delete("Authorization");

  const res = await fetch(`/api/backend/${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  const text = await res.text();

  if (!res.ok) {
    throw new Error(text || `Backend returned ${res.status}`);
  }

  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    throw new Error("Backend returned invalid JSON.");
  }
}

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

export async function linkWallet({ wallet_address }) {
  return privateFetch("wallet/link", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wallet_address }),
  });
}

export async function confirmPermissions(userId) {
  return privateFetch("wallet/confirm-permissions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
}

export async function repairAgent(userId) {
  return privateFetch(
    `agent/repair?user_id=${encodeURIComponent(userId)}`,
    { method: "POST" }
  );
}

export async function deposit(userId, burnTxHash, amount) {
  return privateFetch("bridge/deposit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      burn_tx_hash: burnTxHash,
      amount_usdc_units: amount,
    }),
  });
}

export async function getAgentStatus(userId) {
  return privateFetch(
    `users/${encodeURIComponent(userId)}/agent/status`
  );
}

export async function getAgentProfile(userId) {
  return privateFetch(
    `agent/profile/${encodeURIComponent(userId)}`
  );
}

export async function getAgentHistory(userId) {
  return privateFetch(
    `agent/history/${encodeURIComponent(userId)}`
  );
}

export async function createAgent(userId) {
  return privateFetch("agent/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
}

export async function getDashboard(userId) {
  return privateFetch(
    `users/${encodeURIComponent(userId)}/dashboard`
  );
}

export async function depositParams(amount, hypercoreRecipient) {
  const res = await fetch(`${BACKEND_URL}/bridge/deposit-params`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      amount,
      hypercore_recipient: hypercoreRecipient,
    }),
    cache: "no-store",
  });

  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function bridgeStatus(burnTxHash) {
  const res = await fetch(
    `${BACKEND_URL}/bridge/status/${encodeURIComponent(burnTxHash)}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getMarkets() {
  const res = await fetch(`${BACKEND_URL}/markets`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`backend returned ${res.status}`);
  return res.json();
}

export async function getMarketCandles(
  coin,
  interval = "1h",
  hours = 48
) {
  const res = await fetch(
    `${BACKEND_URL}/agent/markets/${encodeURIComponent(
      coin
    )}/candles?interval=${encodeURIComponent(interval)}&hours=${hours}`,
    { cache: "no-store" }
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
  return n < 1
    ? n.toFixed(4)
    : n.toLocaleString(undefined, {
        maximumFractionDigits: 2,
      });
}

export function fmtVolume(value) {
  const n = parseFloat(value);
  if (Number.isNaN(n)) return "—";
  if (n >= 1_000_000_000)
    return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000)
    return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)
    return `${(n / 1_000).toFixed(1)}K`;
  return n.toFixed(0);
}
