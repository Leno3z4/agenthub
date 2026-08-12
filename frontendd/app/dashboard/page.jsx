"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  Wallet,
  ShieldCheck,
  Activity,
  Plus,
} from "lucide-react";
import { useSession } from "next-auth/react";
import {
  useAccount,
  useWalletClient,
  usePublicClient,
} from "wagmi";

import { depositUSDC } from "@/lib/deposit";
import {
  withdrawHyperliquid,
  transferSpotToPerps,
} from "@/lib/hyperliquid";
import {
  getDashboard,
  getAgentStatus,
} from "@/lib/api";

function StatusDot({ active = false }) {
  return (
    <span
      className={`status-dot ${active ? "status-dot-active" : ""}`}
      aria-hidden="true"
    />
  );
}

async function registerArcWithdrawal({ userId, amount, destination }) {
  const response = await fetch("/api/backend/bridge/withdraw", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      amount_usdc: amount,
      destination,
    }),
    cache: "no-store",
  });

  const text = await response.text();

  if (!response.ok) {
    throw new Error(text || `Withdrawal bridge returned ${response.status}.`);
  }

  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    throw new Error("Withdrawal bridge returned invalid JSON.");
  }
}

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

  const [withdrawalAmount, setWithdrawalAmount] = useState("");
  const [withdrawalLoading, setWithdrawalLoading] = useState(false);
  const [withdrawalError, setWithdrawalError] = useState("");
  const [withdrawalSuccess, setWithdrawalSuccess] = useState("");

  const [transferAmount, setTransferAmount] = useState("");
  const [transferLoading, setTransferLoading] = useState(false);
  const [transferError, setTransferError] = useState("");
  const [transferSuccess, setTransferSuccess] = useState(false);

  const { data: session, status } = useSession();
  const { address } = useAccount();
  const { data: walletClient } = useWalletClient();
  const publicClient = usePublicClient();

  const userId = session?.user?.id || "";

  async function loadDashboard() {
    if (!userId) {
      setNotSetUp(true);
      setLoading(false);
      return;
    }

    try {
      const [dashboardData, agentData] = await Promise.all([
        getDashboard(userId),
        getAgentStatus(userId),
      ]);

      setDashboard(dashboardData);
      setAgent(agentData);
      setError("");
      setNotSetUp(false);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error ? err.message : "Couldn't load your dashboard."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (status !== "authenticated" || !userId) return;

    loadDashboard();

    const interval = setInterval(loadDashboard, 15000);
    return () => clearInterval(interval);
  }, [status, userId, address]);

  async function handleDeposit() {
    if (!userId) {
      setDepositError("Your Alias session is missing.");
      return;
    }

    if (!walletClient || !publicClient || !address) {
      setDepositError("Connect your wallet first.");
      return;
    }

    const amount = Number(depositAmount);

    if (!Number.isFinite(amount) || amount <= 0) {
      setDepositError("Enter a valid USDC amount.");
      return;
    }

    try {
      setDepositLoading(true);
      setDepositError("");
      setDepositSuccess("");

      await depositUSDC({
        walletClient,
        publicClient,
        userId,
        amount,
      });

      setDepositAmount("");
      setDepositSuccess("Deposit submitted successfully.");
      await loadDashboard();
    } catch (err) {
      setDepositError(
        err instanceof Error ? err.message : "Deposit failed."
      );
    } finally {
      setDepositLoading(false);
    }
  }

  async function handleTransferSpotToPerps() {
    const amount = Number(transferAmount);
    const spotAvailable = Number(dashboard?.spot_usdc_available ?? 0);

    if (!Number.isFinite(amount) || amount <= 0) {
      setTransferError("Enter a valid amount.");
      return;
    }

    if (amount > spotAvailable) {
      setTransferError("Amount exceeds available Spot USDC.");
      return;
    }

    try {
      setTransferLoading(true);
      setTransferError("");
      setTransferSuccess(false);

      if (!walletClient) {
        throw new Error(
          "Wallet client is not ready. Try again after the network switches."
        );
      }

      await transferSpotToPerps({
        walletClient,
        amount: amount.toString(),
      });

      setTransferAmount("");
      setTransferSuccess(true);
      await loadDashboard();
    } catch (err) {
      setTransferError(
        err instanceof Error ? err.message : "Spot transfer failed."
      );
    } finally {
      setTransferLoading(false);
    }
  }
  
  async function handleWithdrawal() {
    const amount = Number(withdrawalAmount);
    const walletAddress = address || "";

    if (!Number.isFinite(amount) || amount <= 0) {
      setWithdrawalError("Enter a valid withdrawal amount.");
      return;
    }

    if (!walletAddress) {
      setWithdrawalError("Connect your wallet first.");
      return;
    }

    try {
      setWithdrawalLoading(true);
      setWithdrawalError("");
      setWithdrawalSuccess("");

      if (!walletClient) {
        throw new Error(
          "Wallet client is not ready. Try again after the network switches."
        );
      }

      /*
       * Ask the backend for the current source balance and dynamic
       * CCTP forwarding fee. The backend does NOT receive or hold funds.
       */
      const paramsResponse = await fetch(
        "/api/backend/bridge/withdraw-params",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: userId,
            amount: amount.toString(),
            destination: walletAddress,
          }),
          cache: "no-store",
        }
      );

      const paramsText = await paramsResponse.text();

      if (!paramsResponse.ok) {
        throw new Error(
          paramsText ||
          `Withdrawal parameters failed (${paramsResponse.status}).`
        );
      }

      let params;

      try {
        params = JSON.parse(paramsText);
      } catch {
        throw new Error(
          "Withdrawal parameters returned invalid JSON."
        );
      }

      const withdrawalId = params.withdrawal_id;
      const hyperliquidAmount = params.hyperliquid_amount;
      const sourceDex = params.source_dex ?? "";
      const maximumReceivable = Number(
        params.maximum_receivable ?? 0
      );

      if (!withdrawalId || !hyperliquidAmount) {
        throw new Error(
          "Withdrawal parameters are incomplete."
        );
      }

      if (!Number.isFinite(maximumReceivable)) {
        throw new Error(
          "Withdrawal maximum is invalid."
        );
      }

      /*
       * The user signs ONE Hyperliquid action.
       *
       * The destination is their Arc wallet directly.
       * No Arbitrum address, relay wallet, approval, or backend key.
       */
      const hyperliquidResult = await withdrawHyperliquid({
        walletClient,
        destination: walletAddress,
        amount: hyperliquidAmount,
        sourceDex,
      });

      /*
       * Record the already-submitted Hyperliquid withdrawal.
       * The backend does not perform another blockchain transaction.
       */
      const submitResponse = await fetch(
        "/api/backend/bridge/withdraw",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: userId,
            withdrawal_id: withdrawalId,
            amount: amount.toString(),
            destination: walletAddress,
            hyperliquid_amount: hyperliquidAmount,
            source_dex: sourceDex,
            hyperliquid_result: hyperliquidResult,
          }),
          cache: "no-store",
        }
      );

      const submitText = await submitResponse.text();

      if (!submitResponse.ok) {
        throw new Error(
          submitText ||
          `Withdrawal recording failed (${submitResponse.status}).`
        );
      }

      setWithdrawalAmount("");

      setWithdrawalSuccess(
        "Withdrawal submitted. USDC is being routed from HyperCore through HyperEVM and CCTP to your Arc wallet."
      );

      setTimeout(loadDashboard, 5000);
    } catch (err) {
      setWithdrawalError(
        err instanceof Error
          ? err.message
          : "Withdrawal failed."
      );
    } finally {
      setWithdrawalLoading(false);
    }
  }

  if (notSetUp) {
    return (
      <div className="alias-overview">
        <p className="alias-overview-label">DASHBOARD</p>
        <h1 className="alias-overview-title">Not set up yet.</h1>
        <p className="alias-overview-description">
          No wallet linked yet — there&apos;s nothing to show here until
          onboarding is complete.
        </p>
        <Link href="/onboarding" className="landing-primary">
          Start setup <ArrowUpRight size={18} />
        </Link>
      </div>
    );
  }

  const latest = agent?.latest_action;
  const tradingBalance = Number(dashboard?.usdc_balance ?? 0);
  const marginUsed = Number(dashboard?.margin_used ?? 0);
  const withdrawable = Number(dashboard?.withdrawable ?? 0);
  const spotAvailable = Number(dashboard?.spot_usdc_available ?? 0);

  return (
    <div className="alias-overview">
      <header className="alias-overview-header">
        <div>
          <p className="alias-overview-label">DASHBOARD</p>
          <h1 className="alias-overview-title">Welcome to Alias.</h1>
          <p className="alias-overview-description">
            Alias never decides trades — it executes whatever your agent
            decides. This page shows what&apos;s actually happening, not a
            trading terminal.
          </p>
        </div>

        <div className="alias-status-group">
          <StatusDot active={!!agent?.wallet_connected} />
          <StatusDot active={!!agent?.permissions_approved} />
          <StatusDot active={!!agent?.agent_connected} />
        </div>
      </header>

      {error && (
        <p
          style={{
            color: "#ff6b6b",
            fontSize: "13px",
            marginBottom: "24px",
          }}
        >
          {error}
        </p>
      )}

      {loading ? (
        <p className="alias-overview-description">Loading...</p>
      ) : (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
              gap: "24px",
              alignItems: "stretch",
            }}
          >
            <div className="alias-card">
              <div className="alias-card-icon">
                <Wallet size={20} />
              </div>
              <h3>
                $
                {tradingBalance.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </h3>
              <p>Trading account balance</p>
            </div>

            <div className="alias-card">
              <div className="alias-card-icon">
                <ShieldCheck size={20} />
              </div>
              <h3>
                $
                {marginUsed.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </h3>
              <p>Margin used</p>
            </div>

            <div className="alias-card">
              <div className="alias-card-icon">
                <Activity size={20} />
              </div>
              <h3>{dashboard?.positions?.length ?? 0}</h3>
              <p>Open positions</p>
            </div>
          </div>

          <section className="alias-card" style={{ marginTop: "24px" }}>
            <div className="alias-card-icon">
              <Plus size={20} />
            </div>

            <h2 style={{ marginBottom: "8px" }}>Deposit USDC</h2>

            <p className="alias-overview-description">
              Add more USDC to your HyperCore trading balance.
            </p>

            <div
              style={{
                display: "flex",
                gap: "10px",
                marginTop: "16px",
              }}
            >
              <input
                type="number"
                min="0"
                step="0.01"
                value={depositAmount}
                onChange={(e) => setDepositAmount(e.target.value)}
                placeholder="Amount"
                disabled={depositLoading}
                style={{
                  flex: 1,
                  border: "1px solid var(--line)",
                  borderRadius: "6px",
                  background: "transparent",
                  padding: "10px 12px",
                  color: "inherit",
                }}
              />

              <button
                onClick={handleDeposit}
                disabled={depositLoading || !depositAmount}
                className="landing-primary"
              >
                {depositLoading ? "Depositing..." : "Deposit"}
              </button>
            </div>

            {depositError && (
              <p style={{ color: "#ff6b6b", fontSize: "13px", marginTop: "12px" }}>
                {depositError}
              </p>
            )}

            {depositSuccess && (
              <p style={{ color: "#7ee787", fontSize: "13px", marginTop: "12px" }}>
                {depositSuccess}
              </p>
            )}
          </section>

          <section className="alias-card" style={{ marginTop: "24px" }}>
            <div className="alias-card-icon">
              <Wallet size={20} />
            </div>

            <h2 style={{ marginBottom: "8px" }}>Withdraw USDC</h2>

            <p className="alias-overview-description">
              Withdraw available Hyperliquid USDC directly back to your Arc wallet.
            </p>

            <p className="text-dim" style={{ marginTop: "10px", fontSize: "13px" }}>
              Available: $
              {withdrawable.toLocaleString(undefined, {
                maximumFractionDigits: 2,
              })}
            </p>

            <div
              style={{
                display: "flex",
                gap: "10px",
                marginTop: "16px",
              }}
            >
              <input
                type="number"
                min="0"
                step="0.01"
                value={withdrawalAmount}
                onChange={(e) => setWithdrawalAmount(e.target.value)}
                placeholder="Amount"
                disabled={withdrawalLoading}
                style={{
                  flex: 1,
                  border: "1px solid var(--line)",
                  borderRadius: "6px",
                  background: "transparent",
                  padding: "10px 12px",
                  color: "inherit",
                }}
              />

              <button
                onClick={handleWithdrawal}
                disabled={
                  withdrawalLoading ||
                  !withdrawalAmount ||
                  withdrawable <= 1
                }
                className="landing-primary"
              >
                {withdrawalLoading ? "Routing..." : "Withdraw"}
              </button>
            </div>

            <p className="text-dim" style={{ marginTop: "10px", fontSize: "12px" }}>
              Destination:{" "}
              {address
                ? `${address.slice(0, 6)}...${address.slice(-4)} · Arc`
                : "Arc wallet not connected"}
            </p>

            {withdrawalError && (
              <p style={{ color: "#ff6b6b", fontSize: "13px", marginTop: "12px" }}>
                {withdrawalError}
              </p>
            )}

            {withdrawalSuccess && (
              <p style={{ color: "#7ee787", fontSize: "13px", marginTop: "12px" }}>
                {withdrawalSuccess}
              </p>
            )}
          </section>

          <section className="alias-card" style={{ marginTop: "24px" }}>
            <div className="alias-card-icon">
              <Activity size={20} />
            </div>

            <h2 style={{ marginBottom: "8px" }}>Move Spot USDC</h2>

            <p className="alias-overview-description">
              Move USDC from your Hyperliquid Spot account into Perps so it
              becomes available as trading balance.
            </p>

            <p className="text-dim" style={{ marginTop: "10px", fontSize: "13px" }}>
              Spot available: $
              {spotAvailable.toLocaleString(undefined, {
                maximumFractionDigits: 2,
              })}
            </p>

            <div
              style={{
                display: "flex",
                gap: "10px",
                marginTop: "16px",
              }}
            >
              <input
                type="number"
                min="0"
                step="0.01"
                value={transferAmount}
                onChange={(e) => setTransferAmount(e.target.value)}
                placeholder="Amount"
                disabled={transferLoading}
                style={{
                  flex: 1,
                  border: "1px solid var(--line)",
                  borderRadius: "6px",
                  background: "transparent",
                  padding: "10px 12px",
                  color: "inherit",
                }}
              />

              <button
                onClick={handleTransferSpotToPerps}
                disabled={
                  transferLoading ||
                  !transferAmount ||
                  spotAvailable <= 0
                }
                className="landing-primary"
              >
                {transferLoading ? "Moving..." : "Move to Perps"}
              </button>
            </div>

            {transferError && (
              <p style={{ color: "#ff6b6b", fontSize: "13px", marginTop: "12px" }}>
                {transferError}
              </p>
            )}

            {transferSuccess && (
              <p style={{ color: "#7ee787", fontSize: "13px", marginTop: "12px" }}>
                USDC moved from Spot to Perps.
              </p>
            )}
          </section>

          <section className="alias-next-step">
            <div>
              <span className="alias-next-label">LATEST AGENT ACTION</span>

              {latest ? (
                <>
                  <h2>
                    {latest.is_buy ? "Bought" : "Sold / closed"}{" "}
                    {latest.size} {latest.coin}
                  </h2>
                  <p>
                    {latest.reasoning || "No reasoning reported by the agent."}{" "}
                    {latest.confidence != null &&
                      ` — confidence ${Math.round(
                        latest.confidence * 100
                      )}%`}
                  </p>
                </>
              ) : (
                <>
                  <h2>No actions yet.</h2>
                  <p>
                    Once your agent makes its first trade, it&apos;ll show up
                    here.
                  </p>
                </>
              )}
            </div>

            <Link href="/dashboard/agent" className="landing-primary">
              View agent <ArrowUpRight size={18} />
            </Link>
          </section>
        </>
      )}
    </div>
  );
}
