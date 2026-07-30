export const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function getMarkets() {
  const res = await fetch(`${BACKEND_URL}/markets`, { cache: "no-store" });
  if (!res.ok) throw new Error(`backend returned ${res.status}`);
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
