import { signUserSignedAction } from "@nktkas/hyperliquid";

const EXCHANGE_URL =
  "https://api.hyperliquid-testnet.xyz/exchange";

export async function approveAgent({
  walletClient,
  agentAddress,
}) {
  const nonce = Date.now();

  const action = {
    type: "approveAgent",
    agentAddress,
    agentName: "Alias",
  };

  const signature =
    await signUserSignedAction({
      wallet: walletClient,
      action,
      nonce,
      isTestnet: true,
    });

  const response = await fetch(EXCHANGE_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      action,
      nonce,
      signature,
    }),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}
