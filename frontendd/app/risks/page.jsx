
export default function RiskPage() {
  return (
    <main className="legal-page">
      <div className="legal-content">
        <span className="legal-label">ALIAS / RISK</span>

        <h1>Trading Risk Disclosure</h1>

        <p className="legal-updated">Last updated: August 2026</p>

        <section>
          <h2>Digital Asset Risk</h2>
          <p>
            Digital assets and digital-asset markets can be highly volatile.
            The value of assets can change rapidly and you may lose some or
            all of the funds you use for trading.
          </p>
        </section>

        <section>
          <h2>Perpetuals and Leverage</h2>
          <p>
            Perpetual contracts and leveraged trading carry significant risk.
            Leverage increases exposure relative to the amount of capital
            committed and can cause losses to occur rapidly.
          </p>
          <p>
            Positions may be liquidated automatically when required margin
            levels are not maintained.
          </p>
        </section>

        <section>
          <h2>AI Agent Risk</h2>
          <p>
            Alias allows authorized AI agents to execute trading actions.
            AI systems can produce incorrect outputs, misunderstand
            instructions, react incorrectly to market conditions, or behave
            in ways that were not anticipated by the user.
          </p>
          <p>
            You are responsible for selecting your agent, configuring it,
            providing its instructions, and monitoring its activity.
          </p>
        </section>

        <section>
          <h2>Execution Risk</h2>
          <p>
            Transactions may be delayed, rejected, partially executed, or
            executed at a different price than expected because of market
            conditions, liquidity, latency, network congestion, exchange
            conditions, or technical failures.
          </p>
        </section>

        <section>
          <h2>Blockchain and Smart Contract Risk</h2>
          <p>
            Blockchain networks and smart contracts can contain bugs,
            vulnerabilities, congestion, or other technical failures.
            Blockchain transactions may be irreversible.
          </p>
        </section>

        <section>
          <h2>Third-Party Risk</h2>
          <p>
            Alias relies on third-party infrastructure, including trading
            venues, blockchain networks, bridges, wallets, and AI services.
            Failures or changes to those services may affect your ability to
            use Alias or execute trades.
          </p>
        </section>

        <section>
          <h2>No Guarantee of Profit</h2>
          <p>
            Alias does not guarantee profits, returns, successful trading
            strategies, uninterrupted execution, or protection from losses.
          </p>
        </section>

        <section>
          <h2>Only Risk Funds You Can Afford to Lose</h2>
          <p>
            You should not use funds that you cannot afford to lose. You are
            responsible for determining whether leveraged digital-asset
            trading and AI-controlled execution are appropriate for your
            circumstances.
          </p>
        </section>

        <section>
          <h2>Acknowledgement</h2>
          <p>
            By using Alias and authorizing trading activity, you acknowledge
            that you understand the risks described in this disclosure and
            accept responsibility for your use of the platform.
          </p>
        </section>
      </div>
    </main>
  );
}
