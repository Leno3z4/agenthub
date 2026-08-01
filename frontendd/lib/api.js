export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://localhost:8000";

// ----------------------------------------------------
// Wallet
// ----------------------------------------------------

export async function linkWallet(arcAddress) {
  const res = await fetch(`${BACKEND_URL}/wallet/link`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      arc_address: arcAddress,
    }),
  });

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function confirmPermissions(
  arcAddress,
  apiKey,
) {
  const res = await fetch(
    `${BACKEND_URL}/wallet/confirm-permissions`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        arc_address: arcAddress,
      }),
    }
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

// ----------------------------------------------------
// Bridge
// ----------------------------------------------------

export async function depositParams(
  amount,
) {
  const res = await fetch(
    `${BACKEND_URL}/bridge/deposit-params`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        amount_usdc_units: amount,
      }),
    }
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function deposit(
  arcAddress,
  apiKey,
  burnTxHash,
  amount,
) {
  const res = await fetch(
    `${BACKEND_URL}/bridge/deposit`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        arc_address: arcAddress,
        burn_tx_hash: burnTxHash,
        amount_usdc_units: amount,
      }),
    }
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function bridgeStatus(
  burnTxHash,
) {
  const res = await fetch(
    `${BACKEND_URL}/bridge/status/${burnTxHash}`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

// ----------------------------------------------------
// Agent
// ----------------------------------------------------

export async function agentStatus(
  arcAddress,
  apiKey,
) {
  const res = await fetch(
    `${BACKEND_URL}/agents/${arcAddress}/status`,
    {
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function dashboard(
  arcAddress,
) {
  const res = await fetch(
    `${BACKEND_URL}/dashboard/${arcAddress}`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

// ----------------------------------------------------
// Markets
// ----------------------------------------------------

export async function getMarkets() {
  const res = await fetch(
    `${BACKEND_URL}/markets`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error(
      `backend returned ${res.status}`
    );
  }

  return res.json();
}

// ----------------------------------------------------
// Helpers
// ----------------------------------------------------

export function pctChange(market) {
  const mark = parseFloat(market.mark_price);
  const prev = parseFloat(market.prev_day_price);

  if (!prev) return 0;

  return ((mark - prev) / prev) * 100;
}

export function fmtPrice(value) {
  const n = parseFloat(value);

  if (Number.isNaN(n)) return "—";

  return n < 1
    ? n.toFixed(4)
    : n.toLocaleString(undefined, {
        maximumFractionDigits: 2,
      });
}

export function fmtVolume(value) {
  const n = parseFloat(value);

  if (Number.isNaN(n)) return "—";

  if (n >= 1_000_000_000)
    return `${(n / 1_000_000_000).toFixed(2)}B`;

  if (n >= 1_000_000)
    return `${(n / 1_000_000).toFixed(1)}M`;

  if (n >= 1_000)
    return `${(n / 1_000).toFixed(1)}K`;

  return n.toFixed(0);
}

export async function getDashboard(
  arcAddress,
  apiKey,
) {
  const res = await fetch(
    `${BACKEND_URL}/dashboard/${arcAddress}`,
    {
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      cache: "no-store",
    },
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function getAgentStatus(
  arcAddress,
  apiKey,
) {
  const res = await fetch(
    `${BACKEND_URL}/agents/${arcAddress}/status`,
    {
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      cache: "no-store",
    },
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}
