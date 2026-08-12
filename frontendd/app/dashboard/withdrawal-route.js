/**
 * Frontend entry point for:
 * HyperCore -> HyperEVM -> CCTP -> Arc
 */

export async function startWithdrawal({
  apiBaseUrl,
  amount,
  arcDestination,
}) {
  if (!apiBaseUrl) {
    throw new Error("API base URL is missing.");
  }

  if (!amount || Number(amount) <= 0) {
    throw new Error("Enter a valid withdrawal amount.");
  }

  if (!/^0x[a-fA-F0-9]{40}$/.test(arcDestination || "")) {
    throw new Error("Invalid Arc destination wallet.");
  }

  const response = await fetch(`${apiBaseUrl}/withdrawal`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      amount: String(amount),
      destination: arcDestination,
    }),
  });

  const body = await response.text();

  let data;

  try {
    data = JSON.parse(body);
  } catch {
    throw new Error(
      body || "Withdrawal request failed."
    );
  }

  if (!response.ok) {
    throw new Error(
      data?.detail ||
      data?.message ||
      "Withdrawal request failed."
    );
  }

  return data;
}
