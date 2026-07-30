import Link from "next/link";

/**
 * Transparent on the video hero — a blurred glass strip rather than a
 * solid bar, so the background video stays visible through it.
 */
export default function Nav() {
  return (
    <header className="absolute top-0 left-0 right-0 z-20">
      <div className="max-w-6xl mx-auto px-5 py-5 flex items-center justify-between">
        <Link href="/" className="font-mono tracking-widest text-sm">
          ALIAS
        </Link>
        <nav className="flex items-center gap-8 font-mono text-xs">
          <Link
            href="/onboarding"
            className="text-dim transition-colors duration-150 ease hover-fine:text-white"
          >
            Login
          </Link>
          <Link
            href="/onboarding"
            className="bg-signal text-[#071a2e] font-semibold px-4 py-2 rounded-full
                       transition-transform duration-150 ease-[var(--ease-out)]
                       active:scale-[0.96] hover-fine:brightness-110"
          >
            Launch app
          </Link>
        </nav>
      </div>
    </header>
  );
}
