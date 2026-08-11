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

export const TOKEN_MESSENGER_V2_ABI = [
  {
    type: "function",
    name: "depositForBurnWithHook",
    stateMutability: "nonpayable",
    inputs: [
      { name: "amount", type: "uint256" },
      { name: "destinationDomain", type: "uint32" },
      { name: "mintRecipient", type: "bytes32" },
      { name: "burnToken", type: "address" },
      { name: "destinationCaller", type: "bytes32" },
      { name: "maxFee", type: "uint256" },
      { name: "minFinalityThreshold", type: "uint32" },
      { name: "hookData", type: "bytes" },
    ],
    outputs: [],
  },
];

export const ARC_TOKEN_MESSENGER_V2 =
  "0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA";

export function getUsdcContract(walletClient) {
  return getContract({
    address:
      process.env.NEXT_PUBLIC_ARC_USDC_ADDRESS ||
      "0x3600000000000000000000000000000000000000",
    abi: USDC_ABI,
    client: walletClient,
  });
}

export function getTokenMessengerV2Contract(walletClient) {
  return getContract({
    address: ARC_TOKEN_MESSENGER_V2,
    abi: TOKEN_MESSENGER_V2_ABI,
    client: walletClient,
  });
}
