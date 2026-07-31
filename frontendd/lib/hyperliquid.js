const HL_API =
  "https://api.hyperliquid-testnet.xyz/exchange";

export async function approveAgent({
  walletClient,
  agentAddress,
  agentName = "Alias",
}) {
  const account = walletClient.account;

  if (!account) {
    throw new Error("Wallet not connected.");
  }

  const nonce = Date.now();

  const action = {
    type: "approveAgent",
    hyperliquidChain: "Testnet",
    signatureChainId: "0xa4b1",
    agentAddress,
    agentName,
    nonce,
  };

  const signature = await walletClient.signTypedData({
    account,
    domain: {
      name: "Exchange",
      version: "1",
      chainId: 42161,
    },
    primaryType: "Agent",
    types: {
      Agent: [
        {
          name: "agentAddress",
          type: "address",
        },
        {
          name: "agentName",
          type: "string",
        },
        {
          name: "nonce",
          type: "uint64",
        },
      ],
    },
    message: {
      agentAddress,
      agentName,
      nonce,
    },
  });

  const response = await fetch(HL_API, {
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
