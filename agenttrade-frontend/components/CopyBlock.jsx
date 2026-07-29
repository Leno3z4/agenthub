"use client";
import { useState } from "react";
import { Copy, Check } from "lucide-react";

export default function CopyBlock({ text }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="relative">
      <pre className="text-sm font-mono bg-void border border-line rounded p-4 overflow-x-auto whitespace-pre-wrap">
        {text}
      </pre>
      <button
        onClick={copy}
        className="absolute top-3 right-3 flex items-center gap-1.5 text-xs font-mono px-2 py-1 rounded border border-line text-dim hover-fine:text-white
                   transition-[color,border-color,transform] duration-150 ease-[var(--ease-out)]
                   active:scale-[0.96]"
      >
        {copied ? (
          <Check key="check" size={13} className="text-signal animate-pop-in" />
        ) : (
          <Copy key="copy" size={13} />
        )}
        {copied ? "copied" : "copy"}
      </button>
    </div>
  );
}
