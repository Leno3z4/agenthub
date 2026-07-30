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
      <div className="font-mono tracking-widest text-sm mb-8">ALIAS — SETUP</div>

      <ol className="space-y-1 mb-10">
        {STEPS.map((s, i) => (
          <li
            key={s.title}
            className="flex items-center gap-3 py-2 animate-fade-in-up"
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <span
              className={`w-5 h-5 shrink-0 rounded-full flex items-center justify-center text-[10px] font-mono
                          transition-colors duration-200 ease ${
                i < step
                  ? "bg-signal text-[#071a2e]"
                  : i === step
                  ? "border border-signal text-signal"
                  : "border border-line text-dim"
              }`}
            >
              {i < step ? <Check size={12} className="animate-pop-in" /> : i + 1}
            </span>
            <div>
              <div className={`font-mono text-sm transition-colors duration-200 ease ${i === step ? "text-white" : "text-dim"}`}>
                {s.title}
              </div>
              {i === step && (
                <div className="text-dim text-xs mt-0.5 animate-fade-in-up">{s.desc}</div>
              )}
            </div>
          </li>
        ))}
      </ol>

      <button
        onClick={() => setStep((s) => Math.min(s + 1, STEPS.length))}
        className="w-full bg-signal text-[#071a2e] font-mono font-semibold py-2.5 rounded
                   transition-transform duration-150 ease-[var(--ease-out)]
                   active:scale-[0.97] hover-fine:brightness-110"
      >
        {step < STEPS.length - 1 ? "Continue" : "Enter dashboard"}
      </button>
      <p className="text-dim text-xs font-mono text-center mt-4">
        step logic is a placeholder — wallet connect / approve_agent / OAuth get wired in next
      </p>
    </main>
  );
}
