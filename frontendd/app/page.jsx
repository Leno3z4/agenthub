import Nav from "../components/Nav";
import ProductPreview from "../components/ProductPreview";
import Link from "next/link";

export default function Home() {
  return (
    <main className="landing-page">
      {/* REAL LANDING PAGE VIDEO */}
      <video
        className="landing-video"
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
      >
        <source src="/videos/hero-bg.mp4" type="video/mp4" />
      </video>

      <div className="landing-overlay" />
      <div className="landing-glow" />

      {/* NAV */}
      <Nav />

      {/* HERO */}
      <section className="landing-hero">
        <div className="landing-hero-copy">
          <div className="landing-eyebrow">
            <span className="eyebrow-dot" />
            AUTONOMOUS PERPETUAL INFRASTRUCTURE
          </div>

          <h1>
            Connect your
            <br />
            <span>agent.</span>
            <br />
            Trade the market.
          </h1>

          <p>
            Bring your own wallet, model, and logic.
            Alias is the execution layer between your
            agent and perpetual markets.
          </p>

          <div className="landing-actions">
            <Link href="/onboarding" className="landing-primary">
              Launch app
              <span>↗</span>
            </Link>

            <a href="#system" className="landing-secondary">
              Explore infrastructure
              <span>↓</span>
            </a>
          </div>
        </div>

        {/* PRODUCT PREVIEW */}
        <div className="hero-product">
          <ProductPreview />
        </div>
      </section>

      {/* SYSTEM */}
      <section id="system" className="landing-system">
        <div className="system-heading">
          <span>THE EXECUTION LAYER</span>

          <h2>
            Your agent makes
            <br />
            <em>the decision.</em>
          </h2>

          <p>
            Alias does not make trading decisions for you.
            It provides the infrastructure your agent needs
            to execute its own strategy.
          </p>
        </div>

        <div className="system-grid">
          <div className="system-card">
            <span>01</span>

            <h3>Your wallet</h3>

            <p>
              Connect your wallet and retain control of
              your funds and trading authority.
            </p>
          </div>

          <div className="system-card">
            <span>02</span>

            <h3>Your agent</h3>

            <p>
              Bring Claude, GPT, a self-hosted model,
              or your own trading logic.
            </p>
          </div>

          <div className="system-card">
            <span>03</span>

            <h3>Your execution</h3>

            <p>
              Your agent decides what to do.
              Alias handles the execution layer.
            </p>
          </div>
        </div>
      </section>

      {/* CLOSING CTA */}
      <section className="landing-closing">
        <span>AGENT / MARKET / EXECUTION</span>

        <h2>
          Intelligence
          <br />
          <em>meets execution.</em>
        </h2>

        <Link href="/onboarding" className="landing-primary">
          Enter Alias
          <span>↗</span>
        </Link>
      </section>

      {/* FOOTER */}
      <footer className="landing-footer">
        <span>ALIAS</span>
        <span>Autonomous perpetual infrastructure</span>
        <span>2026</span>
      </footer>
    </main>
  );
}
