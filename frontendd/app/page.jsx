import Link from "next/link";

export default function Home() {
  return (
    <main className="landing-page">
      {/* Landing-page video background */}
      <video
        className="landing-video"
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
        src="/animo-showcase-stream-720p.mp4"
      />

      {/* Cinematic overlay */}
      <div className="landing-overlay" />

      {/* Atmospheric glow */}
      <div className="landing-glow" />

      {/* Navigation */}
      <nav className="landing-nav">
        <Link href="/" className="landing-logo">
          ALIAS
        </Link>

        <div className="landing-nav-right">
          <Link href="/login" className="landing-login">
            Login
          </Link>

          <Link href="/onboarding" className="landing-launch">
            Launch app
          </Link>
        </div>
      </nav>

      {/* Hero */}
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

        {/* Product visual — no fabricated data */}
        <div className="hero-product">
          <div className="product-window">
            <div className="product-window-top">
              <div className="product-brand">
                <span className="product-dot" />
                ALIAS
              </div>

              <div className="product-window-controls">
                <span />
                <span />
                <span />
              </div>
            </div>

            <div className="product-window-body">
              <div className="product-sidebar">
                <div className="sidebar-active" />
                <div />
                <div />
                <div />
                <div />
              </div>

              <div className="product-content">
                <div className="product-placeholder product-wide" />
                <div className="product-placeholder-row">
                  <div className="product-placeholder" />
                  <div className="product-placeholder" />
                </div>
                <div className="product-placeholder product-large" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* System */}
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

      {/* Closing */}
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

      {/* Footer */}
      <footer className="landing-footer">
        <span>ALIAS</span>
        <span>Autonomous perpetual infrastructure</span>
        <span>2026</span>
      </footer>
    </main>
  );
}
