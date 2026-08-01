import { waitForTransactionReceipt } from "viem";

import {
  depositParams,
  deposit,
  bridgeStatus,
} from "./api";

import {
  getUsdcContract,
  getTokenMessengerContract,
} from "./contracts";

export async function depositUSDC({
  walletClient,
  publicClient,
  arcAddress,
  apiKey,
  amount,
}) {
  const params = await depositParams(amount);

  const usdc = getUsdcContract(walletClient);

  const messenger =
    getTokenMessengerContract(walletClient);

  // Approve USDC

  const approveHash =
    await usdc.write.approve([
      process.env.NEXT_PUBLIC_CCTP_TOKEN_MESSENGER,
      BigInt(params.amount),
    ]);

  await waitForTransactionReceipt(publicClient, {
    hash: approveHash,
  });

  // Circle burn

  const burnHash =
    await messenger.write.depositForBurnWithHook([
      BigInt(params.amount),
      params.destinationDomain,
      params.mintRecipient,
      process.env.NEXT_PUBLIC_ARC_USDC_ADDRESS,
      params.destinationCaller,
      BigInt(params.maxFee),
      params.minFinalityThreshold,
      params.hookData,
    ]);

  await waitForTransactionReceipt(publicClient, {
    hash: burnHash,
  });

  await deposit(
    arcAddress,
    apiKey,
    burnHash,
    amount,
  );

  while (true) {
    const status =
      await bridgeStatus(burnHash);

    if (status.complete) {
      return status;
    }

    await new Promise((resolve) =>
      setTimeout(resolve, 5000),
    );
  }
}
