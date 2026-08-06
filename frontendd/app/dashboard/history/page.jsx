"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { getTradeHistory } from "@/lib/api";

function formatTimestamp(value) {
  if (!value) return "—";

  const normalized = value.includes("T")
    ? value
    : `${value.replace(" ", "T")}Z`;

  const date = new Date(normalized);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString();
}

function tradeType(trade) {
  if (trade.is_buy) return "BUY";
  if ((trade.size ?? 0) > 0) return "SELL / CLOSE";
  return "CLOSE";
}

export default function HistoryPage() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notSetUp, setNotSetUp] = useState(false);

  useEffect(() => {
    async function load() {
      const userId = localStorage.getItem("alias_user_id");
      const apiKey = localStorage.getItem("alias_api_key");

      if (!userId || !apiKey) {
        setNotSetUp(true);
        setLoading(false);
        return;
      }

      try {
        const tradeHistory = await getTradeHistory(userId, apiKey);
        setTrades(tradeHistory);
      } catch (err) {
        console.error(err);
        setError(err.message || "Couldn't load trade history.");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-mono text-lg mb-2">Trade history</h1>
        <p className="text-dim text-sm">
          Recorded trade actions from your Alias account, newest first.
        </p>
      </div>

      {notSetUp && (
        <div className="border border-line rounded p-5 bg-surface max-w-2xl space-y-3">
          <div className="font-mono text-sm">No history yet.</div>
          <div className="text-dim text-sm">
            Finish onboarding first so Alias can load history for your account.
          </div>
          <Link href="/onboarding" className="landing-primary inline-flex">
            Start setup
          </Link>
        </div>
      )}

      {error && (
        <div className="border border-warn rounded p-4 bg-surface text-warn text-sm font-mono max-w-2xl">
          {error}
        </div>
      )}

      {!notSetUp && !error && (
        <div className="border border-line rounded bg-surface overflow-hidden">
          {loading ? (
            <div className="text-dim text-sm font-mono py-12 text-center">
              Loading...
            </div>
          ) : trades.length === 0 ? (
            <div className="text-dim text-sm font-mono py-12 text-center">
              No trades recorded yet.
            </div>
          ) : (
            <div className="divide-y divide-[rgba(255,255,255,0.06)]">
              {trades.map((trade) => (
                <div key={trade.id} className="p-4 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="font-mono text-sm">{trade.coin}</span>
                      <span className={`font-mono text-xs ${trade.is_buy ? "text-signal" : "text-warn"}`}>
                        {tradeType(trade)}
                      </span>
                      <span className="text-dim text-xs font-mono">
                        size {trade.size}
                      </span>
                    </div>
                    <div className="text-dim text-xs font-mono">
                      {formatTimestamp(trade.created_at)}
                    </div>
                  </div>

                  {(trade.reasoning || trade.model || trade.strategy || trade.confidence != null) && (
                    <div className="text-sm text-dim space-y-1">
                      {trade.reasoning && <div>{trade.reasoning}</div>}
                      <div className="flex flex-wrap gap-3 text-xs font-mono">
                        {trade.model && <span>model {trade.model}</span>}
                        {trade.strategy && <span>strategy {trade.strategy}</span>}
                        {trade.confidence != null && (
                          <span>confidence {Math.round(trade.confidence * 100)}%</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
