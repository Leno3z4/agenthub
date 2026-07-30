import Link from "next/link";
import Nav from "@/components/Nav";
import ProductPreview from "@/components/ProductPreview";
import { Wallet, Bot, TrendingUp } from "lucide-react";

export default function Home() {
  return (
    <>
      {/* video hero — landing page only */}
      <section className="relative min-h-screen overflow-hidden flex flex-col">
        <video
          className="hero-video absolute inset-0 w-full h-full object-cover"
          src="/videos/hero-bg.mp4"
          autoPlay
          muted
          loop
          playsInline
        />
        {/* dark scrim for legibility + brand-blue glow, replaces raw video color */}
        <div className="absolute inset-0 bg-void/70" />
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(60% 50% at 50% 28%, rgba(79,143,240,0.35), transparent 70%)",
          }}
        />

        <Nav />

        <div className="relative z-10 flex-1 flex flex-col items-center justify-center text-center px-5 pt-20">
          <h1 className="font-mono text-4xl md:text-6xl leading-tight max-w-3xl">
            Connect the agent.
            <br />
            <span className="text-signal">Trade the market.</span>
          </h1>
          <p className="text-dim mt-5 max-w-md">
            Bring your own wallet, model, and logic. Alias is the execution
            layer — it never decides a trade, it just runs what your agent
            already decided.
          </p>
          <Link
            href="/onboarding"
            className="inline-block mt-8 bg-signal text-[#071a2e] font-mono font-semibold px-6 py-3 rounded-full
                       transition-transform duration-150 ease-[var(--ease-out)]
                       active:scale-[0.97] hover-fine:brightness-110"
          >
            Launch app
          </Link>
        </div>

        <div className="relative z-10 px-5 pb-16 mt-16 w-full max-w-2xl mx-auto animate-fade-in-up">
          <ProductPreview />
        </div>
      </section>

      {/* rest of the page — plain dark background, no video */}
      <main className="max-w-5xl mx-auto px-5 py-20">
        <div className="grid md:grid-cols-3 gap-4">
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
      className="animate-fade-in-up border border-line rounded-xl p-5 bg-surface
                 transition-colors duration-200 ease hover-fine:border-signaldim"
      style={{ animationDelay: `${delay}ms` }}
    >
      <Icon size={18} className="text-signal mb-3" />
      <div className="font-mono text-sm mb-2">{title}</div>
      <p className="text-dim text-sm">{text}</p>
    </div>
  );
}
