import { BACKEND_URL } from "./api";

export async function getDepositParams(amount) {
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
    },
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function registerDeposit({
  arcAddress,
  burnTxHash,
  amount,
  apiKey,
}) {
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
    },
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function getBridgeStatus(
  burnTxHash,
) {
  const res = await fetch(
    `${BACKEND_URL}/bridge/status/${burnTxHash}`,
  );

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}
