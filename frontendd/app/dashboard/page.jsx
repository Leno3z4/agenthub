"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Wallet, ShieldCheck, Activity, DollarSign, Plus } from "lucide-react";
import { useAccount, useWalletClient, usePublicClient } from "wagmi";
import { depositUSDC } from "@/lib/deposit";
import StatusDot from "@/components/StatusDot";
import {
  getDashboard,
  getAgentStatus,
  getGatewayBalance,
} from "@/lib/api";

export default function DashboardOverview() {
  const [dashboard, setDashboard] = useState(null);
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notSetUp, setNotSetUp] = useState(false);
  const [depositAmount, setDepositAmount] = useState("");
  const [depositLoading, setDepositLoading] = useState(false);
  const [depositError, setDepositError] = useState("");
  const [depositSuccess, setDepositSuccess] = useState("");
  const { address } = useAccount();
  const { data: walletClient } = useWalletClient();
  const publicClient = usePublicClient();

  async function loadDashboard() {
    const userId = localStorage.getItem("alias_user_id");
    const apiKey = localStorage.getItem("alias_api_key");
    if (!userId || !apiKey) {
      setNotSetUp(true);
      setLoading(false);
      return;
    }
    try {
      const [dashboardData, agentData, gatewayData] = await Promise.all([
        getDashboard(userId, apiKey),
        getAgentStatus(userId, apiKey),
        address
          ? getGatewayBalance(address)
          : Promise.resolve(null),
      ]);
      
      setDashboard({
        ...dashboardData,
        gateway_balance: gatewayData?.total ?? 0,
        gateway_available: gatewayData?.available ?? 0,
        gateway_arc_balance: gatewayData?.arc_balance ?? 0,
      });
     
      setAgent(agentData);
      setError("");
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Couldn't load your dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 15000);
    return () => clearInterval(interval);
  }, [address]);

  async function handleDeposit() {
    const userId = localStorage.getItem("alias_user_id");
    const apiKey = localStorage.getItem("alias_api_key");
    if (!userId || !apiKey) return setDepositError("Your Alias session is missing.");
    if (!walletClient || !publicClient || !address) return setDepositError("Connect your wallet first.");
    const amount = Number(depositAmount);
    if (!Number.isFinite(amount) || amount <= 0) return setDepositError("Enter a valid USDC amount.");

    try {
      setDepositLoading(true);
      setDepositError("");
      setDepositSuccess("");
      await depositUSDC({ walletClient, publicClient, userId, apiKey, amount });
      setDepositAmount("");
      setDepositSuccess("Deposit submitted successfully.");
      await loadDashboard();
    } catch (err) {
      setDepositError(err instanceof Error ? err.message : "Deposit failed.");
    } finally {
      setDepositLoading(false);
    }
  }

  if (notSetUp) {
    return (
      <div className="alias-overview">
        <p className="alias-overview-label">DASHBOARD</p>
        <h1 className="alias-overview-title">Not set up yet.</h1>
        <p className="alias-overview-description">No wallet linked yet — there's nothing to show here until onboarding is complete.</p>
        <Link href="/onboarding" className="landing-primary">Start setup <ArrowUpRight size={18} /></Link>
      </div>
    );
  }

  const latest = agent?.latest_action;
  const gatewayBalance = Number(dashboard?.gateway_balance ?? 0);
  const gatewayAvailable = Number(dashboard?.gateway_available ?? 0);
  const tradingBalance = Number(dashboard?.usdc_balance ?? 0);
  const accountValue = Number(dashboard?.account_value ?? 0);
  const marginUsed = Number(dashboard?.margin_used ?? 0);

  return (
    <div className="alias-overview">
      <header className="alias-overview-header">
        <div>
          <p className="alias-overview-label">DASHBOARD</p>
          <h1 className="alias-overview-title">Welcome to Alias.</h1>
          <p className="alias-overview-description">Alias never decides trades — it executes whatever your agent decides. This page shows what's actually happening, not a trading terminal.</p>
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
            <div className="alias-card">
              <div className="alias-card-icon"><DollarSign size={20} /></div>
              <h3>
                ${gatewayBalance.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </h3>
              <p>Unified USDC balance</p>
              <small className="text-dim">
                ${gatewayAvailable.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })} available
              </small>
            </div>
            <div className="alias-card">
              <div className="alias-card-icon"><Wallet size={20} /></div>
              <h3>
                ${tradingBalance.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </h3>
              <p>Trading account balance</p>
            </div>
            <div className="alias-card">
              <div className="alias-card-icon"><ShieldCheck size={20} /></div>
              <h3>${marginUsed.toLocaleString(undefined, { maximumFractionDigits: 2 })}</h3>
              <p>Margin used</p>
            </div>
            <div className="alias-card">
              <div className="alias-card-icon"><Activity size={20} /></div>
              <h3>{dashboard?.positions?.length ?? 0}</h3>
              <p>Open positions</p>
            </div>
          </section>

          <section className="alias-card" style={{ marginTop: "24px" }}>
            <div className="alias-card-icon"><Plus size={20} /></div>
            <h2 style={{ marginBottom: "8px" }}>Deposit USDC</h2>
            <p className="alias-overview-description">Add more USDC to your HyperCore trading balance.</p>
            <div style={{ display: "flex", gap: "10px", marginTop: "16px" }}>
              <input type="number" min="0" step="0.01" value={depositAmount} onChange={(e) => setDepositAmount(e.target.value)} placeholder="Amount" disabled={depositLoading} style={{ flex: 1, border: "1px solid var(--line)", borderRadius: "6px", background: "transparent", padding: "10px 12px", color: "inherit" }} />
              <button onClick={handleDeposit} disabled={depositLoading || !depositAmount} className="landing-primary">{depositLoading ? "Depositing..." : "Deposit"}</button>
            </div>
            {depositError && <p style={{ color: "#ff6b6b", fontSize: "13px", marginTop: "12px" }}>{depositError}</p>}
            {depositSuccess && <p style={{ color: "#7ee787", fontSize: "13px", marginTop: "12px" }}>{depositSuccess}</p>}
          </section>

          <section className="alias-next-step">
            <div>
              <span className="alias-next-label">LATEST AGENT ACTION</span>
              {latest ? (
                <>
                  <h2>{latest.is_buy ? "Bought" : "Sold / closed"} {latest.size} {latest.coin}</h2>
                  <p>{latest.reasoning || "No reasoning reported by the agent."}{latest.confidence != null && ` — confidence ${Math.round(latest.confidence * 100)}%`}</p>
                </>
              ) : (
                <><h2>No actions yet.</h2><p>Once your agent makes its first trade, it'll show up here.</p></>
              )}
            </div>
            <Link href="/dashboard/agent" className="landing-primary">View agent <ArrowUpRight size={18} /></Link>
          </section>
        </>
      )}
    </div>
  );
}
