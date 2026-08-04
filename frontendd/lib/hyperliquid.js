import { signUserSignedAction } from "@nktkas/hyperliquid/signing";

const EXCHANGE_URL = "https://api.hyperliquid-testnet.xyz/exchange";

export async function approveAgent({ walletClient, agentAddress }) {
  const nonce = Date.now();

  // nonce lives INSIDE the action object, not as a separate param —
  // and signatureChainId / hyperliquidChain are both required for the
  // signature to be valid at all, they were missing entirely before.
  const action = {
    type: "approveAgent",
    signatureChainId: "0x66eee",
    hyperliquidChain: "Testnet",
    agentAddress,
    agentName: "Alias",
    nonce,
  };
  console.log("approveAgent called");
  console.log("walletClient", walletClient);
  console.log("account", walletClient.account);
  console.log("chain", walletClient.chain);
  console.log("agentAddress", agentAddress);
  console.log("about to sign");
  // signUserSignedAction needs the exact EIP-712 field layout for
  // THIS action type — there's no default, it must be passed explicitly.
  const signature = await signUserSignedAction({
    wallet: walletClient,
    action,
    chainId: 5042002,
    types: {
      "HyperliquidTransaction:ApproveAgent": [
        { name: "hyperliquidChain", type: "string" },
        { name: "agentAddress", type: "address" },
        { name: "agentName", type: "string" },
        { name: "nonce", type: "uint64" },
      ],
    },
  });
  console.log("signature", signature);
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

  console.log("STATUS", response.status);

  const body = await response.text();

  console.log(body);

  if (!response.ok) {
    throw new Error(body);
  }

  return JSON.parse(body);}
