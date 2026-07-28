"use client";
import { useState } from "react";
import { Check } from "lucide-react";

const STEPS = [
  { title: "Sign in", desc: "Continue with Google or X" },
  { title: "Connect wallet", desc: "Import your burner wallet" },
  { title: "Authorize", desc: "Grant delegated trading permission — one signature" },
  { title: "Connect your agent", desc: "Get your API endpoint" },
  { title: "Fund wallet", desc: "Deposit trading capital" },
];

export default function Onboarding() {
  const [step, setStep] = useState(0);

  return (
    <main className="max-w-md mx-auto px-5 py-16">
      <div className="font-mono tracking-widest text-sm mb-8">AGENTTRADE — SETUP</div>

      <ol className="space-y-1 mb-10">
        {STEPS.map((s, i) => (
          <li key={s.title} className="flex items-center gap-3 py-2">
            <span
              className={`w-5 h-5 shrink-0 rounded-full flex items-center justify-center text-[10px] font-mono ${
                i < step
                  ? "bg-signal text-[#06201d]"
                  : i === step
                  ? "border border-signal text-signal"
                  : "border border-line text-dim"
              }`}
            >
              {i < step ? <Check size={12} /> : i + 1}
            </span>
            <div>
              <div className={`font-mono text-sm ${i === step ? "text-white" : "text-dim"}`}>
                {s.title}
              </div>
              {i === step && <div className="text-dim text-xs mt-0.5">{s.desc}</div>}
            </div>
          </li>
        ))}
      </ol>

      <button
        onClick={() => setStep((s) => Math.min(s + 1, STEPS.length))}
        className="w-full bg-signal text-[#06201d] font-mono font-semibold py-2.5 rounded"
      >
        {step < STEPS.length - 1 ? "Continue" : "Enter dashboard"}
      </button>
      <p className="text-dim text-xs font-mono text-center mt-4">
        step logic is a placeholder — wallet connect / approve_agent / OAuth get wired in next
      </p>
    </main>
  );
}
