import { getContract } from "viem";

export const USDC_ABI = [
  {
    type: "function",
    name: "approve",
    stateMutability: "nonpayable",
    inputs: [
      { name: "spender", type: "address" },
      { name: "amount", type: "uint256" },
    ],
    outputs: [{ type: "bool" }],
  },
];

export const GATEWAY_WALLET_ABI = [
  {
    type: "function",
    name: "deposit",
    stateMutability: "nonpayable",
    inputs: [
      { name: "token", type: "address" },
      { name: "value", type: "uint256" },
    ],
    outputs: [],
  },
];

export const GATEWAY_WALLET_ADDRESS =
  "0x0077777d7EBA4688BDeF3E311b846F25870A19B9";

export function getUsdcContract(walletClient) {
  return getContract({
    address: process.env.NEXT_PUBLIC_ARC_USDC_ADDRESS,
    abi: USDC_ABI,
    client: walletClient,
  });
}

export function getGatewayWalletContract(walletClient) {
  return getContract({
    address: GATEWAY_WALLET_ADDRESS,
    abi: GATEWAY_WALLET_ABI,
    client: walletClient,
  });
}
