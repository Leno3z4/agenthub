"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAgentStatus } from "@/lib/api";
import { useSession, signOut } from "next-auth/react";

export default function SettingsPage() {
  const [status, setStatus] = useState(null);
  const { data: session, status: authStatus } = useSession();

  useEffect(() => {
    const userId = session?.user?.id;

    if (authStatus !== "authenticated" || !userId) {
      return;
    }

    getAgentStatus(userId)
      .then(setStatus)
      .catch(console.error);
  }, [authStatus, session?.user?.id]);

  async function handleLogout() {
    await signOut({
      callbackUrl: "/onboarding",
    });
  }

  return (
    <div>
      <h1 className="font-mono text-lg mb-6">Settings</h1>

      <div className="border border-line rounded p-5 bg-surface max-w-lg space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-mono text-sm">Network</div>
            <div className="text-dim text-xs">Hyperliquid testnet</div>
          </div>

          <span className="px-3 py-1.5 rounded text-xs font-mono border border-line text-dim">
            TESTNET
          </span>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-line">
          <div>
            <div className="font-mono text-sm">Agent access</div>
            <div className="text-dim text-xs">
              {status?.agent_connected ? "connected" : "not connected"}
            </div>
          </div>

          <Link
            href="/dashboard/agent"
            className="px-3 py-1.5 rounded text-xs font-mono border border-line text-dim hover-fine:text-white"
          >
            manage
          </Link>
        </div>

        <div className="pt-4 border-t border-line text-dim text-xs font-mono leading-5">
          Network switching is intentionally unavailable while Alias is
          testnet-only. Agent authorization is managed through the Hyperliquid
          wallet signature flow.
        </div>

        <div className="pt-4 border-t border-line">
          <button
            type="button"
            onClick={handleLogout}
            className="px-3 py-1.5 rounded text-xs font-mono border border-line text-dim hover-fine:text-white"
          >
            Log out
          </button>
        </div>
      </div>
    </div>
  );
}
