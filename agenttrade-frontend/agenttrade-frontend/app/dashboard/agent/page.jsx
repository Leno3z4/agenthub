export default function AgentPage() {
  return (
    <div>
      <h1 className="font-mono text-lg mb-6">Agent</h1>
      <div className="border border-line rounded p-5 bg-surface max-w-lg">
        <div className="text-dim text-xs font-mono mb-2">API endpoint</div>
        <code className="text-sm font-mono block bg-void border border-line rounded p-3 mb-4">
          POST /agents/&#123;your_address&#125;/trade
        </code>
        <div className="text-dim text-xs font-mono mb-2">status</div>
        <div className="text-dim text-sm font-mono">not connected yet — placeholder</div>
      </div>
    </div>
  );
}
