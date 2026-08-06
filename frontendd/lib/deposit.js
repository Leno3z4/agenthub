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
  userId,
  apiKey,
  amount,
}) {
  const amountUnits = BigInt(
    Math.floor(Number(amount) * 1_000_000)
  );
  
  console.log("INPUT:", amount);
  console.log("MICRO USDC:", amountUnits.toString());
  const params = await depositParams(
    amountUnits.toString()
  );
  console.log({
    frontendAmount: amount,
    backendAmount: params.amount,
    backendMaxFee: params.maxFee,
  });
  const usdc = getUsdcContract(walletClient);

  const messenger =
    getTokenMessengerContract(walletClient);

  // Approve USDC

  const approveHash =
    await usdc.write.approve([
      process.env.NEXT_PUBLIC_CCTP_TOKEN_MESSENGER,
      BigInt(params.amount),
    ]);

  await publicClient.waitForTransactionReceipt({
    hash: approveHash,
  });
  console.log("Deposit params:", params);
  console.log("Sending depositForBurnWithHook...");
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

  await publicClient.waitForTransactionReceipt({
    hash: burnHash,
  });

  await deposit(
    userId,
    apiKey,
    burnHash,
    amountUnits.toString(),
  );

  const started = Date.now();
  
  while (Date.now() - started < 10 * 60 * 1000) {
    const status = await bridgeStatus(burnHash);
  
    console.log("Bridge status:", status);
  
    if (status.complete) {
      return status;
    }
  
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }
  
  throw new Error("Bridge timed out.");
}
