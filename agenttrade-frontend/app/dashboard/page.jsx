import StatusDot from "@/components/StatusDot";

const stats = [
  { label: "Account value", value: "$0.00" },
  { label: "Available margin", value: "$0.00" },
  { label: "Used margin", value: "$0.00" },
  { label: "Unrealized P&L", value: "$0.00" },
];

export default function DashboardOverview() {
  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-mono text-lg">Overview</h1>
        <div className="flex gap-4">
          <StatusDot active label="wallet connected" />
          <StatusDot active={false} label="agent" />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-10">
        {stats.map((s, i) => (
          <div
            key={s.label}
            className="border border-line rounded p-4 bg-surface animate-fade-in-up"
            style={{ animationDelay: `${i * 40}ms` }}
          >
            <div className="text-dim text-xs font-mono mb-1">{s.label}</div>
            <div className="font-mono text-lg">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="border border-line rounded p-5 bg-surface">
        <div className="font-mono text-sm text-dim mb-3">Open positions</div>
        <div className="text-dim text-sm font-mono py-8 text-center">
          no open positions — placeholder, wire to Hyperliquid info endpoint next
        </div>
      </div>
    </div>
  );
}
