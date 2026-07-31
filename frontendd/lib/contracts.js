import {
  getContract,
} from "viem";

export const USDC_ABI = [
  {
    type: "function",
    name: "approve",
    stateMutability: "nonpayable",
    inputs: [
      {
        name: "spender",
        type: "address",
      },
      {
        name: "amount",
        type: "uint256",
      },
    ],
    outputs: [
      {
        type: "bool",
      },
    ],
  },
];

export const TOKEN_MESSENGER_ABI = [
  {
    type: "function",
    name: "depositForBurnWithHook",
    stateMutability: "nonpayable",
    inputs: [
      {
        name: "amount",
        type: "uint256",
      },
      {
        name: "destinationDomain",
        type: "uint32",
      },
      {
        name: "mintRecipient",
        type: "bytes32",
      },
      {
        name: "burnToken",
        type: "address",
      },
      {
        name: "destinationCaller",
        type: "bytes32",
      },
      {
        name: "maxFee",
        type: "uint256",
      },
      {
        name: "minFinalityThreshold",
        type: "uint32",
      },
      {
        name: "hookData",
        type: "bytes",
      },
    ],
    outputs: [],
  },
];

export function getUsdcContract(
  walletClient,
) {
  return getContract({
    address:
      process.env
        .NEXT_PUBLIC_ARC_USDC_ADDRESS,
    abi: USDC_ABI,
    client: walletClient,
  });
}

export function getTokenMessengerContract(
  walletClient,
) {
  return getContract({
    address:
      process.env
        .NEXT_PUBLIC_CCTP_TOKEN_MESSENGER,
    abi: TOKEN_MESSENGER_ABI,
    client: walletClient,
  });
}
