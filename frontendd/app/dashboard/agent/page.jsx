"use client";

import { useEffect, useState } from "react";
import { Copy, RefreshCw } from "lucide-react";
import { getAgentStatus, getAgentProfile } from "@/lib/api";
import { useSession } from "next-auth/react";

export default function AgentPage() {
  const [status, setStatus] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const {
    data: session,
    status,
  } = useSession();
  const userId = session?.user?.id;
  const apiKey = session?.user?.apiKey;
  async function load() {
    const userId = localStorage.getItem("alias_user_id");
    const apiKey = localStorage.getItem("alias_api_key");
    if (!userId || !apiKey) {
      setError("Alias session not found. Complete onboarding first.");
      setLoading(false);
      return;
    }
    try {
      const [statusData, profileData] = await Promise.all([
        getAgentStatus(userId, apiKey),
        getAgentProfile(userId, apiKey),
      ]);
      setStatus(statusData);
      setProfile(profileData);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load agent state.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  async function copyAddress() {
    if (!profile?.agent_address) return;
    await navigator.clipboard.writeText(profile.agent_address);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-mono text-lg">Agent</h1>
        <button onClick={load} disabled={loading} className="px-3 py-1.5 border border-line rounded text-xs font-mono text-dim">
          <RefreshCw size={13} className="inline mr-2" />Refresh
        </button>
      </div>

      {error && <div className="border border-warn rounded p-4 bg-surface text-warn text-sm font-mono mb-5">{error}</div>}

      <div className="border border-line rounded p-5 bg-surface max-w-2xl space-y-5">
        <div>
          <div className="text-dim text-xs font-mono mb-2">CONNECTION</div>
          <div className="font-mono text-sm">{loading ? "checking..." : status?.agent_connected ? "connected" : "not connected"}</div>
          <div className="text-dim text-xs mt-1">{status?.last_seen ? `Last seen ${new Date(status.last_seen).toLocaleString()}` : "No heartbeat recorded yet."}</div>
        </div>

        <div className="pt-4 border-t border-line">
          <div className="text-dim text-xs font-mono mb-2">AGENT WALLET</div>
          <div className="flex gap-2 items-center">
            <code className="text-sm font-mono break-all">{profile?.agent_address || "Not created"}</code>
            {profile?.agent_address && <button onClick={copyAddress} className="border border-line rounded p-2 text-dim"><Copy size={14} /></button>}
          </div>
          {copied && <div className="text-xs text-signal mt-2">Copied</div>}
        </div>

        <div className="pt-4 border-t border-line grid grid-cols-2 gap-4">
          <State label="Wallet" active={profile?.wallet_connected} />
          <State label="Permission" active={profile?.permissions_approved} />
          <State label="Agent" active={status?.agent_connected} />
          <State label="Agent wallet" active={profile?.agent_created} />
        </div>

        <div className="pt-4 border-t border-line">
          <div className="text-dim text-xs font-mono mb-2">TRADING API</div>
          <code className="text-sm font-mono block bg-void border border-line rounded p-3">POST /users/{"{user_id}"}/trade</code>
          <p className="text-dim text-xs mt-2">The connected agent decides the market, direction, size and optional leverage. Alias only executes the request.</p>
        </div>
      </div>
    </div>
  );
}

function State({ label, active }) {
  return <div className="border border-line rounded p-3"><div className="text-dim text-xs font-mono">{label}</div><div className={`font-mono text-sm mt-1 ${active ? "text-signal" : "text-dim"}`}>{active ? "active" : "inactive"}</div></div>;
}
