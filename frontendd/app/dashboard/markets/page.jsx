import Link from "next/link";
import {
  Search,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

import {
  getMarkets,
  pctChange,
  fmtPrice,
  fmtVolume,
} from "@/lib/api";

export default async function MarketsPage() {
  let markets = [];
  let error = null;

  try {
    markets = await getMarkets();
  } catch (e) {
    error = e.message;
  }

  return (
    <div className="alias-markets-page">

      <div className="alias-page-header">
        <div>
          <p className="alias-page-label">
            LIVE MARKETS
          </p>

          <h1>
            Hyperliquid Perpetuals
          </h1>

          <p>
            Browse supported perpetual markets available through
            Hyperliquid execution.
          </p>
        </div>

        <div className="alias-search">
          <Search size={18} />
          <input
            placeholder="Search markets..."
            disabled
          />
        </div>
      </div>

      {error ? (
        <div className="alias-error-card">

          <h3>Backend unavailable</h3>

          <p>{error}</p>

          <span>
            Start the FastAPI server or configure
            NEXT_PUBLIC_BACKEND_URL.
          </span>

        </div>
      ) : (
        <div className="alias-market-table">

          <div className="alias-market-head">
            <span>Market</span>
            <span>Price</span>
            <span>24H</span>
            <span>Volume</span>
          </div>

          {markets.map((market) => {
            const change = pctChange(market);

            return (
              <Link
                key={market.coin}
                href={`/dashboard/markets/${market.coin}`}
                className="alias-market-row"
              >
                <div>
                  <strong>{market.coin}</strong>
                  <small>PERPETUAL</small>
                </div>

                <div>
                  ${fmtPrice(market.mark_price)}
                </div>

                <div
                  className={
                    change >= 0
                      ? "market-positive"
                      : "market-negative"
                  }
                >
                  {change >= 0 ? (
                    <ArrowUpRight size={16} />
                  ) : (
                    <ArrowDownRight size={16} />
                  )}

                  {change >= 0 ? "+" : ""}
                  {change.toFixed(2)}%
                </div>

                <div>
                  {fmtVolume(market.day_volume)}
                </div>
              </Link>
            );
          })}
        </div>
      )}

      <div className="alias-market-footer">
        Live market metadata provided by Hyperliquid.
      </div>

    </div>
  );
}
