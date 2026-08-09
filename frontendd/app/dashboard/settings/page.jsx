"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAgentStatus } from "@/lib/api";
import { signOut } from "next-auth/react";

export default function SettingsPage() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const userId = localStorage.getItem("alias_user_id");
    const apiKey = localStorage.getItem("alias_api_key");
    if (!userId || !apiKey) return;
    getAgentStatus(userId, apiKey).then(setStatus).catch(console.error);
  }, []);
async function handleLogout() {
  localStorage.removeItem("alias_user_id");
  localStorage.removeItem("alias_api_key");
  localStorage.removeItem("alias_agent_address");
  localStorage.removeItem("alias_arc_address");

  await signOut({
    callbackUrl: "/onboarding",
  });
}
  return (
    <div>
      <h1 className="font-mono text-lg mb-6">Settings</h1>
      <div className="border border-line rounded p-5 bg-surface max-w-lg space-y-4">
        <div className="flex items-center justify-between">
          <div><div className="font-mono text-sm">Network</div><div className="text-dim text-xs">Hyperliquid testnet</div></div>
          <span className="px-3 py-1.5 rounded text-xs font-mono border border-line text-dim">TESTNET</span>
        </div>
        <div className="flex items-center justify-between pt-4 border-t border-line">
          <div><div className="font-mono text-sm">Agent access</div><div className="text-dim text-xs">{status?.agent_connected ? "connected" : "not connected"}</div></div>
          <Link href="/dashboard/agent" className="px-3 py-1.5 rounded text-xs font-mono border border-line text-dim hover-fine:text-white">manage</Link>
        </div>
        <div className="pt-4 border-t border-line text-dim text-xs font-mono leading-5">
          Network switching is intentionally unavailable while Alias is testnet-only. Agent authorization is managed through the Hyperliquid wallet signature flow.
        </div>
      </div>
    </div>
    <button onClick={handleLogout}>
      Log out
    </button>
  );
}
