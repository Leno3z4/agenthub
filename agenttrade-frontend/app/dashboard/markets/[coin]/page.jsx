import { notFound } from "next/navigation";
import { getMarkets, pctChange, fmtPrice, fmtVolume } from "@/lib/api";
import CopyBlock from "@/components/CopyBlock";

export default async function CoinDetail({ params }) {
  let markets = [];
  let error = null;
  try {
    markets = await getMarkets();
  } catch (e) {
    error = e.message;
  }

  if (error) {
    return (
      <div className="border border-warn rounded bg-surface p-5 text-warn text-sm font-mono">
        Couldn't reach the backend ({error}). Start it locally or set
        NEXT_PUBLIC_BACKEND_URL, then refresh.
      </div>
    );
  }

  const coin = markets.find((m) => m.coin.toLowerCase() === params.coin.toLowerCase());
  if (!coin) notFound();

  const change = pctChange(coin);
  const funding = parseFloat(coin.funding_rate) * 100;

  const snippet = `POST /agents/{your_address}/trade
{
  "coin": "${coin.coin}",
  "size": <your_size>
}

// direction (is_buy: true/false) is decided by your
// agent's own logic — not set here. This snippet only
// identifies WHICH market to trade.
//
// discover the full tradable universe yourself anytime:
// GET /markets`;

  return (
    <div className="animate-fade-in-up">
      <div className="flex items-baseline justify-between mb-1">
        <h1 className="font-mono text-lg">{coin.coin}-PERP</h1>
        <div className={`font-mono text-sm ${change >= 0 ? "text-signal" : "text-warn"}`}>
          {change >= 0 ? "+" : ""}
          {change.toFixed(2)}%
        </div>
      </div>
      <div className="text-dim text-sm font-mono mb-8">max leverage {coin.max_leverage}x</div>

      <div className="font-mono text-2xl mb-8">${fmtPrice(coin.mark_price)}</div>

      <div className="border border-line rounded bg-surface h-40 flex items-center justify-center mb-8">
        <div className="text-dim text-xs font-mono">
          price chart — wire to Hyperliquid candle (klines) data next
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-10">
        <Stat label="Funding rate" value={`${funding.toFixed(4)}%`} delay={0} />
        <Stat label="Open interest" value={fmtVolume(coin.open_interest)} delay={40} />
        <Stat label="24h volume" value={fmtVolume(coin.day_volume)} delay={80} />
      </div>

      <div className="mb-2 text-dim text-xs font-mono">FOR YOUR AGENT</div>
      <CopyBlock text={snippet} />
    </div>
  );
}

function Stat({ label, value, delay = 0 }) {
  return (
    <div
      className="border border-line rounded p-4 bg-surface animate-fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="text-dim text-xs font-mono mb-1">{label}</div>
      <div className="font-mono text-sm">{value}</div>
    </div>
  );
}
