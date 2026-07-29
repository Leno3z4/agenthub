export default function StatusDot({ active, label }) {
  return (
    <div className="flex items-center gap-2 font-mono text-xs">
      <span
        className={`w-1.5 h-1.5 rounded-full transition-[background-color,box-shadow] duration-200 ease ${
          active ? "bg-signal shadow-[0_0_6px_1px_rgba(79,143,240,0.8)] animate-ambient-pulse" : "bg-dim"
        }`}
      />
      <span className="text-dim">{label}</span>
    </div>
  );
}
