import { notFound } from "next/navigation";
import { getMarkets, getMarketCandles, pctChange, fmtPrice, fmtVolume } from "@/lib/api";
import CopyBlock from "@/components/CopyBlock";

export default async function CoinDetail({ params }) {
  const coinName = typeof params?.then === "function" ? (await params).coin : params.coin;
  let markets = [];
  let candles = [];
  let error = null;
  try {
    markets = await getMarkets();
    candles = (await getMarketCandles(coinName)).candles || [];
  } catch (e) {
    error = e.message;
  }
  if (error && markets.length === 0) return <div className="border border-warn rounded bg-surface p-5 text-warn text-sm font-mono">Couldn't reach the backend ({error}).</div>;

  const coin = markets.find((m) => m.coin.toLowerCase() === coinName.toLowerCase());
  if (!coin) notFound();

  const change = pctChange(coin);
  const funding = parseFloat(coin.funding_rate) * 100;
  const closes = candles.map((c) => Number(c.close)).filter(Number.isFinite);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const width = 760;
  const height = 220;
  const points = closes.map((value, i) => `${(i / Math.max(closes.length - 1, 1)) * width},${height - ((value - min) / range) * (height - 12) - 6}`).join(" ");

  const snippet = `POST /users/{user_id}/trade
{
  "coin": "${coin.coin}",
  "is_buy": true,
  "size": <your_size>,
  "leverage": <optional_leverage>
}

// direction and size are decided by the connected agent.`;

  return (
    <div className="animate-fade-in-up">
      <div className="flex items-baseline justify-between mb-1"><h1 className="font-mono text-lg">{coin.coin}-PERP</h1><div className={`font-mono text-sm ${change >= 0 ? "text-signal" : "text-warn"}`}>{change >= 0 ? "+" : ""}{change.toFixed(2)}%</div></div>
      <div className="text-dim text-sm font-mono mb-8">max leverage {coin.max_leverage}x</div>
      <div className="font-mono text-2xl mb-8">${fmtPrice(coin.mark_price)}</div>

      <div className="border border-line rounded bg-surface p-4 mb-8 overflow-hidden">
        {closes.length > 1 ? <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-56" preserveAspectRatio="none"><polyline fill="none" stroke="currentColor" strokeWidth="2" points={points} className={change >= 0 ? "text-signal" : "text-warn"} /></svg> : <div className="h-56 flex items-center justify-center text-dim text-xs font-mono">No candle data available.</div>}
        <div className="flex justify-between text-dim text-xs font-mono"><span>48h</span><span>1h candles</span></div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-10"><Stat label="Funding rate" value={`${funding.toFixed(4)}%`} /><Stat label="Open interest" value={fmtVolume(coin.open_interest)} /><Stat label="24h volume" value={fmtVolume(coin.day_volume)} /></div>
      <div className="mb-2 text-dim text-xs font-mono">FOR YOUR AGENT</div><CopyBlock text={snippet} />
    </div>
  );
}

function Stat({ label, value }) { return <div className="border border-line rounded p-4 bg-surface"><div className="text-dim text-xs font-mono mb-1">{label}</div><div className="font-mono text-sm">{value}</div></div>; }
