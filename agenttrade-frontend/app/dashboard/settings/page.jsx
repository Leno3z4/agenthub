export default function SettingsPage() {
  const btn =
    "px-3 py-1.5 rounded text-xs font-mono transition-[transform,color,border-color] duration-150 ease-[var(--ease-out)] active:scale-[0.96]";

  return (
    <div>
      <h1 className="font-mono text-lg mb-6">Settings</h1>
      <div className="border border-line rounded p-5 bg-surface max-w-lg space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-mono text-sm">Network</div>
            <div className="text-dim text-xs">testnet</div>
          </div>
          <button className={`${btn} border border-line text-dim hover-fine:text-white`}>
            switch
          </button>
        </div>
        <div className="flex items-center justify-between pt-4 border-t border-line">
          <div>
            <div className="font-mono text-sm">Revoke agent access</div>
            <div className="text-dim text-xs">signs from your wallet — one tx</div>
          </div>
          <button className={`${btn} border border-warn text-warn hover-fine:brightness-110`}>
            revoke
          </button>
        </div>
      </div>
    </div>
  );
}
