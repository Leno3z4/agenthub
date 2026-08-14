"use client";
import Nav from "../components/Nav";
import ProductPreview from "../components/ProductPreview";
import Link from "next/link";
import { useState } from "react";
export default function Home() {
  const [videoReady, setVideoReady] = useState(false);
  const [videoFailed, setVideoFailed] = useState(false);
  return (
    <main className="landing-page">
      {/* REAL LANDING PAGE VIDEO */}
      <video
        className={`landing-video ${videoReady ? "is-ready" : ""}`}
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        aria-hidden="true"
        onCanPlay={() => setVideoReady(true)}
        onError={() => setVideoFailed(true)}
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
          
          </div>
          <h1>
            Connect your
            <br />
            <span>agent.</span>
            <br />
            Trade the market.
          </h1>

          <p>
            Alias is infrastructure for AI agents that trade onchain markets.
            Bring your own wallet, model, and strategy while Alias handles the
            execution layer between your agent and the market.
          </p>

          <div className="landing-actions">
            <Link href="/onboarding" className="landing-primary">
              Launch app
            </Link>

            <a href="#about" className="landing-secondary">
              Learn how it works
            </a>
          </div>
        </div>

        {/* PRODUCT PREVIEW */}
        <div className="hero-product">
          <ProductPreview />
        </div>
      </section>
      <section id="about" className="landing-about">
        <div className="about-label">WHAT IS ALIAS?</div>
      
        <div className="about-content">
          <h2>
            An execution layer
            <br />
            <em>built for agents.</em>
          </h2>
      
          <div className="about-copy">
            <p>
              AI agents can reason about markets, but reasoning alone does not
              execute a trade. Alias connects an agent&apos;s decision-making layer
              to onchain markets through a controlled execution interface.
            </p>
      
            <p>
              You provide the wallet, the agent, and the strategy. Alias provides
              the infrastructure that turns those decisions into actual market
              actions without becoming the decision-maker.
            </p>
          </div>
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
              Bring Claude code , Codex, a self-hosted model,
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
              {/* HOW TO GET STARTED */}
      <section id="guide" className="landing-guide">
        <div className="guide-heading">
          <span>HOW TO GET STARTED</span>

          <h2>
            Get your agent
            <br />
            <em>trading in minutes.</em>
          </h2>

          <p>
            Set up your wallet, connect Alias, fund through Arc, and give your
            agent the instructions it needs to start trading.
          </p>
        </div>

        <div className="guide-grid">
          <div className="guide-card">
            <span>01</span>
            <h3>Set up Hyperliquid</h3>
            <p>
              Create your Hyperliquid mainnet and testnet accounts using the
              same wallet you plan to use with Alias.
            </p>
          </div>

          <div className="guide-card">
            <span>02</span>
            <h3>Connect your wallet</h3>
            <p>
              Connect that wallet to Alias and sign in with Google or X. Your
              wallet and account become linked to your Alias profile.
            </p>
          </div>

          <div className="guide-card">
            <span>03</span>
            <h3>Fund through Arc</h3>
            <p>
              Fund your Hyperliquid account through Arc using CCTP. For
              testing, use Arc testnet and bridge testnet USDC to your
              Hyperliquid testnet account.
            </p>
          </div>

          <div className="guide-card">
            <span>04</span>
            <h3>Connect your agent</h3>
            <p>
              Paste your Alias prompt into your AI agent, provide your Alias
              connection credentials when requested, and authorize the agent.
              Once connected, your agent can execute permitted trades on your
              behalf.
            </p>
          </div>
        </div>
      </section>
        <Link href="/onboarding" className="landing-primary">
          Enter Alias
        </Link>
      </section>

      {/* FOOTER */}
      <footer className="landing-footer">
        <span>ALIAS</span>
      
        <div className="landing-footer-links">
          <Link href="/terms">Terms</Link>
          <Link href="/privacy">Privacy</Link>
          <Link href="/risk">Risk Disclosure</Link>
        </div>
      
        <span>2026</span>
      </footer>
    </main>
  );
}
