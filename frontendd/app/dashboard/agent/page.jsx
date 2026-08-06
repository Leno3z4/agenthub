"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import StatusDot from "@/components/StatusDot";
import { getAgentStatus } from "@/lib/api";

function formatTimestamp(value) {
  if (!value) return "Never";

  const normalized = value.includes("T")
    ? value
    : `${value.replace(" ", "T")}Z`;

  const date = new Date(normalized);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString();
}

function latestActionLabel(action) {
  if (!action) return "No actions recorded yet.";
  if (action.is_buy) return `Bought ${action.size} ${action.coin}`;
  if ((action.size ?? 0) > 0) return `Sold / closed ${action.size} ${action.coin}`;
  return `Closed ${action.coin}`;
}

export default function AgentPage() {
  const [agent, setAgent] = useState(null);
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
        const agentStatus = await getAgentStatus(userId, apiKey);
        setAgent(agentStatus);
      } catch (err) {
        console.error(err);
        setError(err.message || "Couldn't load agent status.");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const latest = agent?.latest_action;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-mono text-lg mb-2">Agent</h1>
        <p className="text-dim text-sm">
          Live status for the delegated trading agent tied to your Alias account.
        </p>
      </div>

      {notSetUp && (
        <div className="border border-line rounded p-5 bg-surface max-w-2xl space-y-3">
          <div className="font-mono text-sm">No agent connected yet.</div>
          <div className="text-dim text-sm">
            Finish onboarding first so Alias can store your <code>user_id</code> and <code>api_key</code> locally.
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

      {!notSetUp && (
        <>
          <div className="border border-line rounded p-5 bg-surface max-w-2xl space-y-4">
            <div className="text-dim text-xs font-mono">LIVE STATUS</div>
            {loading ? (
              <div className="text-dim text-sm font-mono">Loading...</div>
            ) : (
              <>
                <div className="alias-status-group">
                  <StatusDot active={!!agent?.wallet_connected} label="Wallet" />
                  <StatusDot active={!!agent?.permissions_approved} label="Approved" />
                  <StatusDot active={!!agent?.agent_connected} label="Agent" />
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  <div className="border border-line rounded p-4 bg-void">
                    <div className="text-dim text-xs font-mono mb-1">Last seen</div>
                    <div className="font-mono text-sm">{formatTimestamp(agent?.last_seen)}</div>
                  </div>

                  <div className="border border-line rounded p-4 bg-void">
                    <div className="text-dim text-xs font-mono mb-1">Latest action</div>
                    <div className="font-mono text-sm">{latestActionLabel(latest)}</div>
                  </div>
                </div>

                {latest?.reasoning && (
                  <div className="border border-line rounded p-4 bg-void">
                    <div className="text-dim text-xs font-mono mb-1">Latest reasoning</div>
                    <div className="text-sm">{latest.reasoning}</div>
                    {latest.confidence != null && (
                      <div className="text-dim text-xs font-mono mt-2">
                        Confidence {Math.round(latest.confidence * 100)}%
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          <div className="border border-line rounded p-5 bg-surface max-w-2xl">
            <div className="text-dim text-xs font-mono mb-2">API endpoint</div>
            <code className="text-sm font-mono block bg-void border border-line rounded p-3 mb-4 whitespace-pre-wrap">
              {`POST /users/{user_id}/trade
Authorization: Bearer <api_key>`}
            </code>
            <div className="text-dim text-xs font-mono mb-2">Route key</div>
            <div className="text-dim text-sm font-mono">
              Use the Alias <code>user_id</code> returned during onboarding — not the wallet address.
            </div>
          </div>
        </>
      )}
    </div>
  );
}
