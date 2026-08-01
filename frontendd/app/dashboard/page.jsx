"use client";

import StatusDot from "@/components/StatusDot";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getDashboard,
  getAgentStatus,
} from "@/lib/api";
import {
  ArrowUpRight,
  Wallet,
  Bot,
  ShieldCheck,
  Activity,
} from "lucide-react";



export default function DashboardOverview() {
  return (
    <div className="alias-overview">
      <header className="alias-overview-header">
        <div>
          <p className="alias-overview-label">
            DASHBOARD
          </p>

          <h1 className="alias-overview-title">
            Welcome to Alias.
          </h1>

          <p className="alias-overview-description">
            Connect your wallet, authorize your execution key,
            and bring your own AI. Alias never decides trades—
            it simply executes the strategy your agent produces.
          </p>
        </div>

        <div className="alias-status-group">
          <StatusDot active label="Wallet" />
          <StatusDot active={false} label="Agent" />
        </div>
      </header>

      <section className="alias-setup-grid">
        {cards.map(({ icon: Icon, title, description }) => (
          <div key={title} className="alias-card">
            <div className="alias-card-icon">
              <Icon size={20} />
            </div>

            <h3>{title}</h3>

            <p>{description}</p>
          </div>
        ))}
      </section>

      <section className="alias-next-step">
        <div>
          <span className="alias-next-label">
            NEXT STEP
          </span>

          <h2>
            Finish configuring your trading infrastructure.
          </h2>

          <p>
            Once your wallet, execution key, and AI provider are
            connected, you'll be able to execute trades through
            Hyperliquid using your own autonomous strategy.
          </p>
        </div>

        <Link
          href="/onboarding"
          className="landing-primary"
        >
          Continue setup
          <ArrowUpRight size={18} />
        </Link>
      </section>
    </div>
  );
}

const [dashboard, setDashboard] = useState(null);

const [agent, setAgent] = useState(null);

const [loading, setLoading] = useState(true);

useEffect(() => {
  async function load() {
    try {
      const arcAddress =
        localStorage.getItem(
          "alias_arc_address",
        );

      const apiKey =
        localStorage.getItem(
          "alias_api_key",
        );

      if (!arcAddress || !apiKey) return;

      const [dashboardData, agentData] =
        await Promise.all([
          getDashboard(
            arcAddress,
            apiKey,
          ),
          getAgentStatus(
            arcAddress,
            apiKey,
          ),
        ]);

      setDashboard(
        dashboardData,
      );

      setAgent(
        agentData,
      );
    } finally {
      setLoading(false);
    }
  }

  load();
}, []);
