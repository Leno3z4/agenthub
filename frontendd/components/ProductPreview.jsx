import { TrendingUp, TrendingDown, Bot } from "lucide-react";

const rows = [
  { coin: "BTC", price: "67,420.15", change: "+1.8%", up: true },
  { coin: "ETH", price: "3,184.62", change: "-0.9%", up: false },
  { coin: "SOL", price: "178.34", change: "+4.2%", up: true },
];

export default function ProductPreview() {
  return (
    <div className="rounded-xl border border-white/10 bg-surface/70 backdrop-blur-xl shadow-2xl overflow-hidden">
      <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-white/10">
        <div className="p-5">
          <div className="text-dim text-xs font-mono mb-3">MARKETS</div>
          <div className="space-y-2.5">
            {rows.map((r) => (
              <div key={r.coin} className="flex items-center justify-between font-mono text-sm gap-3">
                <span>{r.coin}-PERP</span>
                <span className="text-dim">${r.price}</span>
                <span
                  className={`flex items-center gap-1 text-xs shrink-0 ${
                    r.up ? "text-signal" : "text-warn"
                  }`}
                >
                  {r.up ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  {r.change}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="p-5">
          <div className="text-dim text-xs font-mono mb-3">AGENT</div>
          <div className="flex items-center gap-2 mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-signal shadow-[0_0_6px_1px_rgba(79,143,240,0.8)] animate-ambient-pulse" />
            <span className="font-mono text-sm">connected</span>
          </div>
          <div className="flex items-center gap-2 text-dim font-mono text-xs mb-1">
            <Bot size={13} /> last action
          </div>
          <div className="font-mono text-sm mb-4">opened SOL-PERP long, 2.4x</div>
          <div className="text-dim font-mono text-xs mb-1">unrealized P&L</div>
          <div className="font-mono text-lg text-signal">+$412.60</div>
        </div>
      </div>
    </div>
  );
}
