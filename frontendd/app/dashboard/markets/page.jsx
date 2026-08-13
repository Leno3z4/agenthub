"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import {
  getMarkets,
  pctChange,
  fmtPrice,
  fmtVolume,
} from "@/lib/api";

export default function MarketsPage() {
  const [markets, setMarkets] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getMarkets()
      .then(setMarkets)
      .catch((err) =>
        setError(
          err instanceof Error
            ? err.message
            : "Backend unavailable"
        )
      )
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();

    if (!q) return markets;

    return markets.filter((market) =>
      market.coin.toLowerCase().includes(q)
    );
  }, [markets, query]);

  return (
    <div className="alias-markets-page">
      <div className="alias-page-header">
        <div>
          <p className="alias-page-label">
            LIVE MARKETS
          </p>

          <h1>Hyperliquid Perpetuals</h1>

          <p>
            Browse supported perpetual markets available
            through Hyperliquid execution.
          </p>
        </div>

        <div className="alias-search">
          <Search size={18} />

          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search markets..."
          />
        </div>
      </div>

      {error ? (
        <div className="alias-error-card">
          <h3>Backend unavailable</h3>
          <p>{error}</p>
        </div>
      ) : loading ? (
        <div className="text-dim font-mono py-12">
          Loading markets...
        </div>
      ) : (
        <div className="alias-market-table">
          <div className="alias-market-head">
            <span>Market</span>
            <span>Price</span>
            <span>24H</span>
            <span>Volume</span>
          </div>

          {filtered.map((market) => {
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
                  {change >= 0 ? "+" : ""}
                  {change.toFixed(2)}%
                </div>

                <div>
                  {fmtVolume(market.day_volume)}
                </div>
              </Link>
            );
          })}

          {filtered.length === 0 && (
            <div className="text-dim font-mono py-12 text-center">
              No markets match “{query}”.
            </div>
          )}
        </div>
      )}

      <div className="alias-market-footer">
        Live market metadata provided by Hyperliquid.
      </div>
    </div>
  );
}
