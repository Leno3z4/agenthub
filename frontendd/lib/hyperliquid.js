import { signUserSignedAction } from "@nktkas/hyperliquid/signing";

const EXCHANGE_URL = "https://api.hyperliquid-testnet.xyz/exchange";

// Hyperliquid Testnet EIP-712 signing chain for normal Hyperliquid actions.
const TESTNET_SIGNATURE_CHAIN_ID = "0x66eee";
const TESTNET_CHAIN_ID = 421614;

// Arc Testnet destination values.
// Arc EVM chain ID: 5042002 = 0x4cef52
// Arc CCTP domain: 26
const ARC_TESTNET_SIGNATURE_CHAIN_ID = "0x4cef52";
const ARC_TESTNET_CHAIN_ID = 5042002;
const ARC_TESTNET_CCTP_DOMAIN = 26;

async function submitUserAction({
  walletClient,
  action,
  types,
  signingChainId = TESTNET_CHAIN_ID,
}) {
  if (!walletClient) throw new Error("Wallet is not connected.");
  if (!walletClient.account) {
    throw new Error("Wallet account is unavailable.");
  }

  const signature = await signUserSignedAction({
    wallet: walletClient,
    action,
    types,
    chainId: signingChainId,
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

  if (!response.ok) {
    throw new Error(body || `Hyperliquid request failed (${response.status}).`);
  }

  let parsed;

  try {
    parsed = JSON.parse(body);
  } catch {
    throw new Error(body);
  }

  if (parsed?.status === "err") {
    throw new Error(
      parsed.response || "Hyperliquid rejected the action."
    );
  }

  return parsed;
}


export async function approveAgent({
  walletClient,
  agentAddress,
}) {
  if (!agentAddress) {
    throw new Error("Agent address is required.");
  }

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


export async function transferSpotToPerps({
  walletClient,
  amount,
}) {
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


/**
 * Withdraw USDC:
 *
 * HyperCore -> HyperEVM -> CCTP -> Arc
 *
 * The linked user wallet signs this action directly.
 * There is no Arbitrum relay wallet and no backend withdrawal key.
 *
 * sourceDex:
 *   ""      = Hyperliquid perp balance
 *   "spot"  = Hyperliquid Spot balance
 */
export async function withdrawHyperliquid({
  walletClient,
  destination,
  amount,
  sourceDex = "",
}) {
  if (!destination) {
    throw new Error(
      "Arc withdrawal destination is missing."
    );
  }

  if (!/^0x[a-fA-F0-9]{40}$/.test(destination)) {
    throw new Error(
      "Invalid Arc withdrawal destination."
    );
  }

  const numericAmount = Number(amount);

  if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
    throw new Error("Enter a valid withdrawal amount.");
  }

  if (sourceDex !== "" && sourceDex !== "spot") {
    throw new Error("Invalid Hyperliquid withdrawal source.");
  }

  const nonce = Date.now();

  return submitUserAction({
    walletClient,
    signingChainId: ARC_TESTNET_CHAIN_ID,
    action: {
      type: "sendToEvmWithData",
      hyperliquidChain: "Testnet",
      signatureChainId: ARC_TESTNET_SIGNATURE_CHAIN_ID,
      token: "USDC",
      amount: String(amount),
      sourceDex,
      destinationRecipient: destination,
      addressEncoding: "hex",
      destinationChainId: ARC_TESTNET_CCTP_DOMAIN,
      gasLimit: 200000,
      data: "0x",
      nonce,
    },
    types: {
      "HyperliquidTransaction:SendToEvmWithData": [
        { name: "hyperliquidChain", type: "string" },
        { name: "token", type: "string" },
        { name: "amount", type: "string" },
        { name: "sourceDex", type: "string" },
        { name: "destinationRecipient", type: "string" },
        { name: "addressEncoding", type: "string" },
        { name: "destinationChainId", type: "uint32" },
        { name: "gasLimit", type: "uint64" },
        { name: "data", type: "bytes" },
        { name: "nonce", type: "uint64" },
      ],
    },
  });
}
