import { signUserSignedAction } from "@nktkas/hyperliquid/signing";

const EXCHANGE_URL =
  "https://api.hyperliquid-testnet.xyz/exchange";

const TESTNET_SIGNATURE_CHAIN_ID = "0x66eee";
const TESTNET_CHAIN_ID = 421614;
const WITHDRAWAL_FEE = 1;

const APPROVE_AGENT_TYPES = {
  "HyperliquidTransaction:ApproveAgent": [
    { name: "hyperliquidChain", type: "string" },
    { name: "agentAddress", type: "address" },
    { name: "agentName", type: "string" },
    { name: "nonce", type: "uint64" },
  ],
};

const USD_CLASS_TRANSFER_TYPES = {
  "HyperliquidTransaction:UsdClassTransfer": [
    { name: "hyperliquidChain", type: "string" },
    { name: "amount", type: "string" },
    { name: "toPerp", type: "bool" },
    { name: "nonce", type: "uint64" },
  ],
};

const WITHDRAW_TYPES = {
  "HyperliquidTransaction:Withdraw": [
    { name: "hyperliquidChain", type: "string" },
    { name: "destination", type: "string" },
    { name: "amount", type: "string" },
    { name: "time", type: "uint64" },
  ],
};

function getNonce() {
  return Date.now();
}

function validateWalletClient(walletClient) {
  if (!walletClient) {
    throw new Error("Wallet is not connected.");
  }

  if (!walletClient.account?.address) {
    throw new Error("Wallet account is unavailable.");
  }

  if (typeof walletClient.signTypedData !== "function") {
    throw new Error(
      "Connected wallet does not support EIP-712 signing."
    );
  }
}

function validateAddress(address, fieldName = "address") {
  if (
    typeof address !== "string" ||
    !/^0x[a-fA-F0-9]{40}$/.test(address)
  ) {
    throw new Error(`Invalid ${fieldName}.`);
  }
}

function validateAmount(amount, fieldName = "amount") {
  const numeric = Number(amount);

  if (
    amount === undefined ||
    amount === null ||
    amount === "" ||
    !Number.isFinite(numeric) ||
    numeric <= 0
  ) {
    throw new Error(`Enter a valid ${fieldName}.`);
  }

  return numeric;
}

async function submitUserAction({
  walletClient,
  action,
  types,
}) {
  validateWalletClient(walletClient);

  const signature = await signUserSignedAction({
    wallet: walletClient,
    action,
    types,
    chainId: TESTNET_CHAIN_ID,
  });

  const response = await fetch(EXCHANGE_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      action,
      nonce: action.nonce ?? action.time,
      signature,
    }),
  });

  const body = await response.text();

  let parsed;

  try {
    parsed = JSON.parse(body);
  } catch {
    throw new Error(
      body || `Hyperliquid returned HTTP ${response.status}.`
    );
  }

  if (!response.ok) {
    throw new Error(
      parsed?.response ||
        parsed?.error ||
        `Hyperliquid returned HTTP ${response.status}.`
    );
  }

  if (parsed?.status === "err") {
    throw new Error(
      parsed.response ||
        "Hyperliquid rejected the action."
    );
  }

  return parsed;
}

export async function approveAgent({
  walletClient,
  agentAddress,
}) {
  validateWalletClient(walletClient);
  validateAddress(agentAddress, "agent address");

  const nonce = getNonce();

  const action = {
    type: "approveAgent",
    signatureChainId: TESTNET_SIGNATURE_CHAIN_ID,
    hyperliquidChain: "Testnet",
    agentAddress,
    agentName: "Alias",
    nonce,
  };

  return submitUserAction({
    walletClient,
    action,
    types: APPROVE_AGENT_TYPES,
  });
}

export async function transferSpotToPerps({
  walletClient,
  amount,
}) {
  validateWalletClient(walletClient);
  validateAmount(amount, "transfer amount");

  const nonce = getNonce();

  const action = {
    type: "usdClassTransfer",
    signatureChainId: TESTNET_SIGNATURE_CHAIN_ID,
    hyperliquidChain: "Testnet",
    amount: String(amount),
    toPerp: true,
    nonce,
  };

  return submitUserAction({
    walletClient,
    action,
    types: USD_CLASS_TRANSFER_TYPES,
  });
}

export async function withdrawHyperliquid({
  walletClient,
  destination,
  amount,
}) {
  if (!walletClient) {
    throw new Error("Wallet is not connected.");
  }

  if (!walletClient.account) {
    throw new Error("Wallet account is unavailable.");
  }

  if (!destination) {
    throw new Error("No withdrawal destination is linked.");
  }

  if (!/^0x[a-fA-F0-9]{40}$/.test(destination)) {
    throw new Error("Invalid withdrawal destination.");
  }

  const numericAmount = Number(amount);

  if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
    throw new Error("Enter a valid withdrawal amount.");
  }

  const nonce = Date.now();

  const action = {
    type: "withdraw3",
    signatureChainId: TESTNET_SIGNATURE_CHAIN_ID,
    hyperliquidChain: "Testnet",
    destination,
    amount: String(amount),
    time: nonce,
  };

  return submitUserAction({
    walletClient,
    action,
    types: {
      "HyperliquidTransaction:Withdraw": [
        {
          name: "hyperliquidChain",
          type: "string",
        },
        {
          name: "destination",
          type: "string",
        },
        {
          name: "amount",
          type: "string",
        },
        {
          name: "time",
          type: "uint64",
        },
      ],
    },
  });
}
