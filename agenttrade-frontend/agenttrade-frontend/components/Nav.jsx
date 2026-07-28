import Link from "next/link";

export default function Nav() {
  return (
    <header className="border-b border-line">
      <div className="max-w-5xl mx-auto px-5 py-4 flex items-center justify-between">
        <Link href="/" className="font-mono tracking-widest text-sm">
          AGENTTRADE
        </Link>
        <nav className="flex items-center gap-6 font-mono text-xs text-dim">
          <Link href="/onboarding" className="hover:text-white transition-colors">
            Launch app
          </Link>
        </nav>
      </div>
    </header>
  );
}
