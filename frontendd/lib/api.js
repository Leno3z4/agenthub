export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "https://agenthub-wine.vercel.app";

// ----------------------------------------------------
// User
// ----------------------------------------------------

export async function registerUser(data) {
  console.log("Sending registration", data);

  const res = await fetch(`${BACKEND_URL}/users/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  console.log("Status:", res.status);

  const text = await res.text();
  console.log("Body:", text);

  if (!res.ok) {
    throw new Error(text);
  }

  return JSON.parse(text);
}
// ----------------------------------------------------
// Wallet
// ----------------------------------------------------

export async function linkWallet({
  user_id,
  google_id,
  email,
  name,
  picture,
  wallet_address,
}) {
  const res = await fetch(`${BACKEND_URL}/wallet/link`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id,
      google_id,
      email,
      name,
      picture,
      wallet_address,
    }),
  });

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function confirmPermissions(
  userId,
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
        user_id: userId,
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
  userId,
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
        user_id: userId,
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
  userId,
  apiKey,
) {
  const res = await fetch(
    `${BACKEND_URL}/agents/${userId}/status`,
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
  userId,
) {
  const res = await fetch(
    `${BACKEND_URL}/users/${userId}/dashboard`,
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
  userId,
  apiKey,
) {
  const res = await fetch(
    `${BACKEND_URL}/dashboard/${userId}`,
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
  userId,
  apiKey,
) {
  const res = await fetch(
    `${BACKEND_URL}/users/${userId}/agent/status`,
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
