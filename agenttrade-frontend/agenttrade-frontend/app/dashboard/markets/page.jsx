import Link from "next/link";
import { getMarkets, pctChange, fmtPrice, fmtVolume } from "@/lib/api";

export default async function MarketsPage() {
  let markets = [];
  let error = null;
  try {
    markets = await getMarkets();
  } catch (e) {
    error = e.message;
  }

  return (
    <div>
      <h1 className="font-mono text-lg mb-6">Markets</h1>

      {error ? (
        <div className="border border-warn rounded bg-surface p-5 text-warn text-sm font-mono">
          Couldn't reach the backend ({error}). Make sure it's running locally
          (uvicorn main:app --reload) or that NEXT_PUBLIC_BACKEND_URL points
          at your deployed backend, then refresh.
        </div>
      ) : (
        <>
          <div className="border border-line rounded bg-surface overflow-hidden">
            <div className="grid grid-cols-4 px-5 py-3 text-dim text-xs font-mono border-b border-line">
              <div>Market</div>
              <div className="text-right">Price</div>
              <div className="text-right">24h</div>
              <div className="text-right">Volume</div>
            </div>
            {markets.map((m) => {
              const change = pctChange(m);
              return (
                <Link
                  key={m.coin}
                  href={`/dashboard/markets/${m.coin}`}
                  className="grid grid-cols-4 px-5 py-3 text-sm font-mono hover:bg-surface2 transition-colors border-b border-line last:border-0"
                >
                  <div>{m.coin}-PERP</div>
                  <div className="text-right">${fmtPrice(m.mark_price)}</div>
                  <div className={`text-right ${change >= 0 ? "text-signal" : "text-warn"}`}>
                    {change >= 0 ? "+" : ""}
                    {change.toFixed(2)}%
                  </div>
                  <div className="text-right text-dim">{fmtVolume(m.day_volume)}</div>
                </Link>
              );
            })}
          </div>
          <p className="text-dim text-xs font-mono mt-3">live from Hyperliquid</p>
        </>
      )}
    </div>
  );
}
