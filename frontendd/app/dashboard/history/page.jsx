"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { getAgentHistory } from "@/lib/api";

export default function HistoryPage() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const { data: session, status } = useSession();
  const userId = session?.user?.id;

  async function load() {
    if (status === "loading") return;

    if (!userId) {
      setError("Alias session not found. Complete onboarding first.");
      setLoading(false);
      return;
    }

    try {
      const data = await getAgentHistory(userId);
      setTrades(data?.trades || []);
      setError("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load trade history."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (status === "loading") return;

    load();

    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [status, userId]);

  return (
    <div>
      <h1 className="font-mono text-lg mb-6">Trade history</h1>

      {error && (
        <div className="border border-warn rounded p-4 bg-surface text-warn text-sm font-mono mb-5">
          {error}
        </div>
      )}

      <div className="border border-line rounded bg-surface overflow-hidden">
        {loading ? (
          <div className="text-dim text-sm font-mono py-12 text-center">
            Loading trade history...
          </div>
        ) : trades.length === 0 ? (
          <div className="text-dim text-sm font-mono py-12 text-center">
            No trades recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-mono">
              <thead>
                <tr className="border-b border-line text-dim text-xs">
                  <th className="text-left p-4">Time</th>
                  <th className="text-left p-4">Market</th>
                  <th className="text-left p-4">Action</th>
                  <th className="text-left p-4">Size</th>
                  <th className="text-left p-4">Confidence</th>
                  <th className="text-left p-4">Model</th>
                </tr>
              </thead>

              <tbody>
                {trades.map((trade) => (
                  <tr
                    key={trade.id}
                    className="border-b border-line last:border-0"
                  >
                    <td className="p-4 text-dim">
                      {trade.created_at
                        ? new Date(trade.created_at).toLocaleString()
                        : "—"}
                    </td>

                    <td className="p-4">{trade.coin}</td>

                    <td
                      className={`p-4 ${
                        trade.is_buy ? "text-signal" : "text-warn"
                      }`}
                    >
                      {trade.is_buy ? "BUY" : "CLOSE / SELL"}
                    </td>

                    <td className="p-4">{trade.size}</td>

                    <td className="p-4">
                      {trade.confidence == null
                        ? "—"
                        : `${Math.round(trade.confidence * 100)}%`}
                    </td>

                    <td className="p-4 text-dim">
                      {trade.model || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
