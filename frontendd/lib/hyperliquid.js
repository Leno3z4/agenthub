import { signUserSignedAction } from "@nktkas/hyperliquid/signing";

const EXCHANGE_URL = "https://api.hyperliquid-testnet.xyz/exchange";
const TESTNET_SIGNATURE_CHAIN_ID = "0x66eee";
const TESTNET_CHAIN_ID = 421614;

async function submitUserAction({ walletClient, action, types }) {
  if (!walletClient) throw new Error("Wallet is not connected.");
  if (!walletClient.account) throw new Error("Wallet account is unavailable.");

  const signature = await signUserSignedAction({
    wallet: walletClient,
    action,
    types,
    chainId: TESTNET_CHAIN_ID,
  });

  const response = await fetch(EXCHANGE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action,
      nonce: action.nonce ?? action.time,
      signature,
    }),
  });

  const body = await response.text();
  if (!response.ok) throw new Error(body);

  let parsed;
  try {
    parsed = JSON.parse(body);
  } catch {
    throw new Error(body);
  }

  if (parsed?.status === "err") {
    throw new Error(parsed.response ?? "Hyperliquid rejected the action.");
  }

  return parsed;
}

export async function approveAgent({ walletClient, agentAddress }) {
  if (!agentAddress) throw new Error("Agent address is required.");
  const nonce = Date.now();

  return submitUserAction({
    walletClient,
    action: {
      type: "approveAgent",
      signatureChainId: TESTNET_SIGNATURE_CHAIN_ID,
      hyperliquidChain: "Testnet",
      agentAddress,
      agentName: "Alias",
      nonce,
    },
    types: {
      "HyperliquidTransaction:ApproveAgent": [
        { name: "hyperliquidChain", type: "string" },
        { name: "agentAddress", type: "address" },
        { name: "agentName", type: "string" },
        { name: "nonce", type: "uint64" },
      ],
    },
  });
}

export async function transferSpotToPerps({ walletClient, amount }) {
  const nonce = Date.now();

  return submitUserAction({
    walletClient,
    action: {
      type: "usdClassTransfer",
      signatureChainId: TESTNET_SIGNATURE_CHAIN_ID,
      hyperliquidChain: "Testnet",
      amount: String(amount),
      toPerp: true,
      nonce,
    },
    types: {
      "HyperliquidTransaction:UsdClassTransfer": [
        { name: "hyperliquidChain", type: "string" },
        { name: "amount", type: "string" },
        { name: "toPerp", type: "bool" },
        { name: "nonce", type: "uint64" },
      ],
    },
  });
}

/*
 * Low-level Hyperliquid withdrawal helper only.
 * The dashboard withdrawal flow should call the backend route instead,
 * so the user experiences one operation:
 * HyperCore -> Arbitrum -> CCTP -> Arc.
 */
export async function withdrawHyperliquid({
  walletClient,
  destination,
  amount,
}) {
  if (!destination) throw new Error("Hyperliquid withdrawal destination is missing.");
  if (!/^0x[a-fA-F0-9]{40}$/.test(destination)) {
    throw new Error("Invalid Hyperliquid withdrawal destination.");
  }

  const numericAmount = Number(amount);
  if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
    throw new Error("Enter a valid withdrawal amount.");
  }

  const time = Date.now();

  return submitUserAction({
    walletClient,
    action: {
      type: "withdraw3",
      signatureChainId: TESTNET_SIGNATURE_CHAIN_ID,
      hyperliquidChain: "Testnet",
      destination,
      amount: String(amount),
      time,
    },
    types: {
      "HyperliquidTransaction:Withdraw": [
        { name: "hyperliquidChain", type: "string" },
        { name: "destination", type: "string" },
        { name: "amount", type: "string" },
        { name: "time", type: "uint64" },
      ],
    },
  });
}
