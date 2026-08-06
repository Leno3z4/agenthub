export default function AgentPage() {
  return (
    <div>
      <h1 className="font-mono text-lg mb-6">Agent</h1>
      <div className="border border-line rounded p-5 bg-surface max-w-lg">
        <div className="text-dim text-xs font-mono mb-2">API endpoint</div>
        <code className="text-sm font-mono block bg-void border border-line rounded p-3 mb-4 whitespace-pre-wrap">
          {`POST /users/{your_user_id}/trade
Authorization: Bearer <api_key>`}
        </code>
        <div className="text-dim text-xs font-mono mb-2">route key</div>
        <div className="text-dim text-sm font-mono mb-4">
          Use the Alias <code>user_id</code> returned during onboarding — not the wallet address.
        </div>
        <div className="text-dim text-xs font-mono mb-2">status</div>
        <div className="text-dim text-sm font-mono">not connected yet — placeholder</div>
      </div>
    </div>
  );
}
