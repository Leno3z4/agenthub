import Link from "next/link";
import Nav from "@/components/Nav";
import { Wallet, Bot, TrendingUp } from "lucide-react";

export default function Home() {
  return (
    <>
      <Nav />
      <main className="max-w-5xl mx-auto px-5 py-20">
        <h1 className="font-mono text-3xl md:text-4xl leading-tight max-w-2xl">
          Connect your own AI agent.
          <br />
          Trade perpetuals on your terms.
        </h1>
        <p className="text-dim mt-5 max-w-xl">
          AgentTrade is infrastructure, not a trader. Bring your wallet,
          your model, your logic — we just execute what your agent decides.
        </p>
        <Link
          href="/onboarding"
          className="inline-block mt-8 bg-signal text-[#071a2e] font-mono font-semibold px-5 py-3 rounded
                     transition-transform duration-150 ease-[var(--ease-out)]
                     active:scale-[0.97] hover-fine:brightness-110"
        >
          Launch app
        </Link>

        <div className="grid md:grid-cols-3 gap-4 mt-20">
          <FeatureCard
            icon={Wallet}
            title="Your wallet"
            text="Connect your own burner wallet. We never touch your private key or hold your funds."
            delay={0}
          />
          <FeatureCard
            icon={Bot}
            title="Your agent"
            text="Claude, GPT, a self-hosted model, custom code — any agent can trade through our API."
            delay={60}
          />
          <FeatureCard
            icon={TrendingUp}
            title="Your logic"
            text="Every trade originates from your agent's decisions. We only execute what's authorized."
            delay={120}
          />
        </div>
      </main>
    </>
  );
}

function FeatureCard({ icon: Icon, title, text, delay = 0 }) {
  return (
    <div
      className="animate-fade-in-up border border-line rounded p-5 bg-surface"
      style={{ animationDelay: `${delay}ms` }}
    >
      <Icon size={18} className="text-signal mb-3" />
      <div className="font-mono text-sm mb-2">{title}</div>
      <p className="text-dim text-sm">{text}</p>
    </div>
  );
}
