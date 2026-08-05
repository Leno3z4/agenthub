"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Wallet, ShieldCheck, Activity } from "lucide-react";
import StatusDot from "@/components/StatusDot";
import { getDashboard, getAgentStatus } from "@/lib/api";

export default function DashboardOverview() {
  const [dashboard, setDashboard] = useState(null);
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
        const [dashboardData, agentData] = await Promise.all([
          getDashboard(userId, apiKey),
          getAgentStatus(userId, apiKey),
        ]);
        setDashboard(dashboardData);
        setAgent(agentData);
      } catch (err) {
        console.error(err);
        setError(err.message || "Couldn't load your dashboard.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (notSetUp) {
    return (
      <div className="alias-overview">
        <p className="alias-overview-label">DASHBOARD</p>
        <h1 className="alias-overview-title">Not set up yet.</h1>
        <p className="alias-overview-description">No wallet linked yet, there's nothing to show here until onboarding is complete.</p>
        <Link href="/onboarding" className="landing-primary">Start setup <ArrowUpRight size={18} /></Link>
      </div>
    );
  }

  const latest = agent?.latest_action;
  return (
    <div className="alias-overview">
      <header className="alias-overview-header">
        <div>
          <p className="alias-overview-label">DASHBOARD</p>
          <h1 className="alias-overview-title">Welcome to Alias.</h1>
          <p className="alias-overview-description">Alias never decides trades, it executes whatever your agent decides. This page shows what's actually happening, not a trading terminal.</p>
        </div>
        <div className="alias-status-group">
          <StatusDot active={!!agent?.wallet_connected} label="Wallet" />
          <StatusDot active={!!agent?.permissions_approved} label="Approved" />
          <StatusDot active={!!agent?.agent_connected} label="Agent" />
        </div>
      </header>

      {error && <p style={{ color: "#ff6b6b", fontSize: "13px", marginBottom: "24px" }}>{error}</p>}
      {loading ? <p className="alias-overview-description">Loading...</p> : (
        <>
          <section className="alias-setup-grid">
            <div className="alias-card"><div className="alias-card-icon"><Wallet size={20} /></div><h3>${Number(dashboard?.account_value ?? 0).toLocaleString()}</h3><p>Account value</p></div>
            <div className="alias-card"><div className="alias-card-icon"><ShieldCheck size={20} /></div><h3>${Number(dashboard?.margin_used ?? 0).toLocaleString()}</h3><p>Margin used</p></div>
            <div className="alias-card"><div className="alias-card-icon"><Activity size={20} /></div><h3>{dashboard?.positions?.length ?? 0}</h3><p>Open positions</p></div>
          </section>
          <section className="alias-next-step">
            <div>
              <span className="alias-next-label">LATEST AGENT ACTION</span>
              {latest ? <><h2>{latest.is_buy ? "Bought" : "Sold / closed"} {latest.size} {latest.coin}</h2><p>{latest.reasoning || "No reasoning reported by the agent."}{latest.confidence != null && `, confidence ${Math.round(latest.confidence * 100)}%`}</p></> : <><h2>No actions yet.</h2><p>Once your agent makes its first trade, it'll show up here.</p></>}
            </div>
            <Link href="/dashboard/agent" className="landing-primary">View agent <ArrowUpRight size={18} /></Link>
          </section>
        </>
      )}
    </div>
  );
}
