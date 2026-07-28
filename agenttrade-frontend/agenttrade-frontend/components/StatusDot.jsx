export default function StatusDot({ active, label }) {
  return (
    <div className="flex items-center gap-2 font-mono text-xs">
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          active ? "bg-signal shadow-[0_0_6px_1px_rgba(73,214,200,0.8)]" : "bg-dim"
        }`}
      />
      <span className="text-dim">{label}</span>
    </div>
  );
}
